"""
Pipeline distribué Spark — Urban Data Explorer
=================================================
Démontre :
  - C1.3 : Data Lake (HDFS) intégrant des sources variées (CSV + JSON)
  - C2.2 : Traitement distribué sur un cluster Spark (2 workers)
  - C2.4 : Mesure de performance du pipeline

Ce script :
  1. Lit le gold CSV (PostgreSQL export) et le JSON (MongoDB export)
  2. Les écrit dans HDFS en couches Bronze / Silver / Gold
  3. Effectue un traitement distribué (agrégation répartie sur les workers)
  4. Mesure et affiche le temps d'exécution
"""

import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, sum as spark_sum, count, round as spark_round

# ──────────────────────────────────────────────────────────
# 1. INITIALISATION DE LA SESSION SPARK (cluster distribué)
# ──────────────────────────────────────────────────────────

spark = SparkSession.builder \
    .appName("UrbanDataExplorer_PipelineDistribue") \
    .master("spark://spark-master:7077") \
    .config("spark.executor.memory", "1g") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 70)
print("PIPELINE DISTRIBUÉ — URBAN DATA EXPLORER")
print("=" * 70)
print(f"Spark version : {spark.version}")
print(f"Master        : {spark.sparkContext.master}")
print(f"Executors     : {spark.sparkContext.defaultParallelism} partitions par défaut")
print()

debut_total = time.time()

# ──────────────────────────────────────────────────────────
# 2. INGESTION SOURCES VARIÉES → COUCHE BRONZE (HDFS)
# ──────────────────────────────────────────────────────────

print("[1/4] Ingestion des sources variées (CSV + JSON) → Bronze HDFS...")
debut = time.time()

# Source 1 : CSV (données structurées issues de PostgreSQL/Gold)
df_gold = spark.read.csv("/source/dashboard_gold_complet.csv", header=True, inferSchema=True, sep=";")
print(f"  ✓ CSV chargé : {df_gold.count()} lignes, {len(df_gold.columns)} colonnes")

# Source 2 : JSON (données semi-structurées issues de MongoDB)
df_transport = spark.read.json("/source/transport_details.json")
print(f"  ✓ JSON chargé : {df_transport.count()} documents")

# Écriture en Bronze (données brutes, format Parquet pour optimisation)
df_gold.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/bronze/gold_csv")
df_transport.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/bronze/transport_json")

duree = time.time() - debut
print(f"  ✓ Écrit dans HDFS : /datalake/bronze/ (durée : {duree:.2f}s)")
print()

# ──────────────────────────────────────────────────────────
# 3. TRANSFORMATION DISTRIBUÉE → COUCHE SILVER (HDFS)
# ──────────────────────────────────────────────────────────

print("[2/4] Transformation distribuée → Silver HDFS...")
debut = time.time()

# Forcer la répartition sur plusieurs partitions pour bien utiliser les 2 workers
df_gold_repartitioned = df_gold.repartition(4)

# Jointure entre les deux sources (CSV structuré + JSON semi-structuré)
df_silver = df_gold_repartitioned.join(
    df_transport,
    df_gold_repartitioned["arrondissement"] == df_transport["arrondissement"],
    "left"
).select(
    df_gold_repartitioned["arrondissement"],
    col("prix_m2_median_2024"),
    col("population_2022"),
    col("revenu_median"),
    col("indice_accessibilite"),
    col("indice_tension_sociale"),
    col("metro.nb_stations").alias("nb_stations_metro_json"),
    col("metro.trafic_annuel").alias("trafic_metro_json")
)

df_silver.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/silver/arrondissements_enrichis")

duree = time.time() - debut
print(f"  ✓ Jointure CSV+JSON effectuée et écrite dans /datalake/silver/ (durée : {duree:.2f}s)")
print(f"  ✓ Nombre de partitions utilisées : {df_silver.rdd.getNumPartitions()}")
print()

# ──────────────────────────────────────────────────────────
# 4. AGRÉGATION DISTRIBUÉE → COUCHE GOLD (HDFS)
# ──────────────────────────────────────────────────────────

print("[3/4] Agrégation distribuée sur le cluster → Gold HDFS...")
debut = time.time()

# Catégoriser les arrondissements par niveau de prix (calcul distribué)
df_categorise = df_silver.withColumn(
    "categorie_prix",
    col("prix_m2_median_2024").cast("int")
)

df_stats_globales = df_categorise.agg(
    spark_round(avg("prix_m2_median_2024"), 0).alias("prix_m2_moyen_paris"),
    spark_round(avg("revenu_median"), 0).alias("revenu_moyen_paris"),
    spark_round(avg("indice_accessibilite"), 2).alias("accessibilite_moyenne"),
    spark_sum("population_2022").alias("population_totale_paris"),
    count("arrondissement").alias("nb_arrondissements")
)

df_stats_globales.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/gold/stats_paris")

duree = time.time() - debut
print(f"  ✓ Agrégation distribuée écrite dans /datalake/gold/ (durée : {duree:.2f}s)")
print()

print("  Résultat de l'agrégation distribuée :")
df_stats_globales.show(truncate=False)

# ──────────────────────────────────────────────────────────
# 5. PREUVE DE DISTRIBUTION SUR LES WORKERS
# ──────────────────────────────────────────────────────────

print("[4/4] Vérification de la distribution sur les workers Spark...")
status_tracker = spark.sparkContext.statusTracker()
executor_infos = status_tracker.getExecutorInfos()
print(f"  ✓ Nombre d'executors actifs sur le cluster : {len(executor_infos)}")
for info in executor_infos:
    print(f"     - {info.host}:{info.port}")
duree_totale = time.time() - debut_total
print()
print("=" * 70)
print(f"✅ PIPELINE TERMINÉ — Durée totale : {duree_totale:.2f}s")
print("=" * 70)
print()
print("Structure du Data Lake créée dans HDFS :")
print("  /datalake/bronze/gold_csv          (CSV structuré, format Parquet)")
print("  /datalake/bronze/transport_json    (JSON semi-structuré, format Parquet)")
print("  /datalake/silver/arrondissements_enrichis  (jointure multi-sources)")
print("  /datalake/gold/stats_paris         (agrégats finaux)")
print()
print("Vérifie dans l'interface HDFS : http://localhost:9870/explorer.html#/datalake")
print("=" * 70)

spark.stop()