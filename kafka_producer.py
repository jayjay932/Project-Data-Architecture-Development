#!/usr/bin/env python3
"""
Kafka Producer — Urban Data Explorer
======================================
Simule l'arrivée en temps réel de nouvelles transactions DVF
(Demandes de Valeurs Foncières) sur le topic Kafka 'dvf-transactions'.

Dans un cas réel de production, ce producer serait déclenché par
l'API data.gouv.fr dès qu'une nouvelle transaction est publiée.
Ici, on simule 20 transactions (une par arrondissement) avec un
délai de 2 secondes entre chaque — pour démontrer le streaming.

Usage :
    pip install kafka-python
    python kafka_producer.py
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BROKER = "localhost:9092"
TOPIC = "dvf-transactions"

# Données simulées réalistes basées sur les prix médians réels
PRIX_PAR_ARRONDISSEMENT = {
    1: 12586, 2: 11444, 3: 12000, 4: 12932, 5: 12000,
    6: 14981, 7: 14620, 8: 12500, 9: 10712, 10: 9373,
    11: 10000, 12: 9000, 13: 8848, 14: 9464, 15: 9642,
    16: 11122, 17: 10236, 18: 8858, 19: 7986, 20: 8372
}

TYPES_LOCAUX = ["Appartement", "Appartement", "Appartement", "Maison"]
TYPOLOGIES = ["T1", "T2", "T2", "T3", "T3", "T4", "T5plus"]


def generer_transaction(arrondissement):
    """Génère une transaction DVF simulée pour un arrondissement donné"""
    prix_m2_base = PRIX_PAR_ARRONDISSEMENT[arrondissement]
    # Variation aléatoire de ±15% autour du prix médian
    variation = random.uniform(0.85, 1.15)
    prix_m2 = int(prix_m2_base * variation)

    surface = random.randint(20, 120)
    valeur_fonciere = prix_m2 * surface

    return {
        "id_transaction": f"DVF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{arrondissement}",
        "date_mutation": datetime.now().isoformat(),
        "arrondissement": arrondissement,
        "code_postal": f"750{arrondissement:02d}",
        "type_local": random.choice(TYPES_LOCAUX),
        "nombre_pieces": random.choice(TYPOLOGIES),
        "surface_reelle_bati": surface,
        "valeur_fonciere": valeur_fonciere,
        "prix_m2": prix_m2,
        "source": "DVF_streaming_simulation"
    }


def main():
    print("=" * 60)
    print("KAFKA PRODUCER — Transactions DVF en streaming")
    print("=" * 60)
    print(f"Broker    : {KAFKA_BROKER}")
    print(f"Topic     : {TOPIC}")
    print(f"Intervalle: 2 secondes entre chaque transaction")
    print()

    # Connexion au broker Kafka
    print("Connexion au broker Kafka...")
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8")
    )
    print("✓ Connecté à Kafka\n")

    # Envoi des transactions (une par arrondissement, puis boucle)
    nb_envois = 0
    try:
        while True:
            for arrondissement in range(1, 21):
                transaction = generer_transaction(arrondissement)

                # Envoi dans le topic Kafka (clé = numéro arrondissement)
                future = producer.send(
                    TOPIC,
                    key=arrondissement,
                    value=transaction
                )
                result = future.get(timeout=10)

                nb_envois += 1
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Transaction envoyée → "
                    f"Arr. {arrondissement:2d}e | "
                    f"{transaction['type_local']:11s} | "
                    f"{transaction['surface_reelle_bati']:3d}m² | "
                    f"{transaction['prix_m2']:,}€/m² | "
                    f"Total: {transaction['valeur_fonciere']:,}€"
                )

                time.sleep(2)  # 1 transaction toutes les 2 secondes

    except KeyboardInterrupt:
        print(f"\n⏹ Producer arrêté. {nb_envois} transactions envoyées.")
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
