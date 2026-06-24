#!/usr/bin/env python3
"""
Kafka Consumer — Spark Structured Streaming — Urban Data Explorer
==================================================================
Démontre C2.2 : système de streaming temps réel

Ce script :
1. Lit le topic Kafka 'dvf-transactions' en continu
2. Traite les données en micro-batch toutes les 10 secondes
3. Calcule le prix/m² médian par arrondissement en temps réel
4. Insère les résultats dans PostgreSQL (table streaming_dvf)

Usage (depuis le conteneur Spark Master) :
    spark-submit \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0,org.postgresql:postgresql:42.3.1 \
      /source/kafka_consumer_spark.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, avg, count,
    window, current_timestamp, round as spark_round
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType, FloatType, TimestampType
)

KAFKA_BROKER = "kafka-paris:29092"
TOPIC = "dvf-transactions"
PG_URL = "jdbc:postgresql://postgres-paris:5432/urban_data_explorer"
PG_PROPS = {
    "user": "paris_admin",
    "password": "paris2024",
    "driver": "org.postgresql.Driver"
}

# Schéma des messages Kafka (JSON)
SCHEMA = StructType([
    StructField("id_transaction", StringType()),
    StructField("date_mutation", StringType()),
    StructField("arrondissement", IntegerType()),
    StructField("code_postal", StringType()),
    StructField("type_local", StringType()),
    StructField("nombre_pieces", StringType()),
    StructField("surface_reelle_bati", IntegerType()),
    StructField("valeur_fonciere", FloatType()),
    StructField("prix_m2", FloatType()),
    StructField("source", StringType())
])


def ecrire_dans_postgres(batch_df, batch_id):
    """
    Fonction appelée pour chaque micro-batch :
    calcule les agrégats et les écrit dans PostgreSQL
    """
    if batch_df.count() == 0:
        return

    print(f"\n{'='*60}")
    print(f"MICRO-BATCH #{batch_id} reçu — {batch_df.count()} transactions")
    print(f"{'='*60}")

    # Afficher les transactions brutes du batch
    batch_df.select(
        "arrondissement", "type_local",
        "surface_reelle_bati", "prix_m2", "valeur_fonciere"
    ).show(truncate=False)

    # Calculer les agrégats par arrondissement
    aggregats = batch_df.groupBy("arrondissement").agg(
        spark_round(avg("prix_m2"), 0).alias("prix_m2_moyen_streaming"),
        spark_round(avg("valeur_fonciere"), 0).alias("valeur_moyenne_streaming"),
        count("*").alias("nb_transactions_streaming")
    ).withColumn("batch_id", col("arrondissement") * 0 + batch_id) \
     .withColumn("timestamp_traitement", current_timestamp())

    print("Agrégats calculés par arrondissement :")
    aggregats.show(truncate=False)

    # Écrire dans PostgreSQL
    aggregats.write \
        .mode("append") \
        .jdbc(PG_URL, "streaming_dvf", properties=PG_PROPS)

    print(f"✓ Batch #{batch_id} écrit dans PostgreSQL (table: streaming_dvf)")


def main():
    print("=" * 60)
    print("SPARK STRUCTURED STREAMING — Kafka → PostgreSQL")
    print("=" * 60)
    print(f"Source  : Kafka topic '{TOPIC}'")
    print(f"Sink    : PostgreSQL table 'streaming_dvf'")
    print(f"Trigger : micro-batch toutes les 10 secondes")
    print()

    spark = SparkSession.builder \
        .appName("UrbanDataExplorer_KafkaStreaming") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "512m") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Lecture du stream Kafka
    df_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # Désérialisation du JSON
    df_parsed = df_stream.select(
        from_json(col("value").cast("string"), SCHEMA).alias("data"),
        col("timestamp")
    ).select("data.*", "timestamp")

    # Écriture en micro-batch (foreachBatch)
    query = df_parsed.writeStream \
        .foreachBatch(ecrire_dans_postgres) \
        .trigger(processingTime="10 seconds") \
        .option("checkpointLocation", "/tmp/checkpoint_dvf") \
        .start()

    print("✓ Stream démarré — en attente de transactions Kafka...")
    print("  (Lancez kafka_producer.py dans un autre terminal)")
    print("  Ctrl+C pour arrêter\n")

    query.awaitTermination()


if __name__ == "__main__":
    main()
