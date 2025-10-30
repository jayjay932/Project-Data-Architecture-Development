#!/usr/bin/env python3
"""
Outil diagnostic pour un fichier CSV :
- détecte les colonnes entièrement vides
- comptabilise les valeurs manquantes par colonne
- repère les doublons exacts et les identifiants répétés
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Tuple


MISSING_TOKENS = {"", "na", "nan", "none"}


def is_missing(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    return stripped.lower() in MISSING_TOKENS


def normalize_row(fieldnames: Iterable[str], row: dict) -> Tuple[Tuple[str, str], ...]:
    # Normalise une ligne pour pouvoir compter les doublons exacts
    return tuple((field, (row.get(field) or "").strip()) for field in fieldnames)


def analyse_csv(path: Path, top_n: int) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        total_rows = 0
        missing_counts: Counter[str] = Counter()
        duplicate_rows: Counter[Tuple[Tuple[str, str], ...]] = Counter()
        id_counts: Counter[str] = Counter()

        for row in reader:
            total_rows += 1
            duplicate_rows[normalize_row(fieldnames, row)] += 1

            id_value = row.get("id_mutation")
            if id_value:
                id_counts[id_value] += 1

            for field in fieldnames:
                if is_missing(row.get(field)):
                    missing_counts[field] += 1

    print(f"Fichier analysé : {path}")
    print(f"Nombre de lignes : {total_rows}")
    print(f"Nombre de colonnes : {len(fieldnames)}")

    empty_columns = [col for col in fieldnames if missing_counts[col] == total_rows]
    if empty_columns:
        print("\nColonnes entièrement vides :")
        for col in empty_columns:
            print(f"  - {col}")
    else:
        print("\nAucune colonne entièrement vide.")

    if missing_counts:
        print("\nColonnes avec le plus de valeurs manquantes :")
        for column, count in missing_counts.most_common(top_n):
            pct = (count / total_rows * 100) if total_rows else 0
            print(f"  - {column}: {count} valeurs manquantes ({pct:.1f} %)")

    duplicate_row_count = sum(count - 1 for count in duplicate_rows.values() if count > 1)
    print(f"\nNombre de doublons exacts : {duplicate_row_count}")
    if duplicate_row_count:
        print(f"Top {min(top_n, len(duplicate_rows))} doublons :")
        shown = 0
        for row_key, count in duplicate_rows.most_common():
            if count <= 1 or shown >= top_n:
                break
            print(f"  - {count} occurrences pour la ligne : {dict(row_key)}")
            shown += 1

    if id_counts:
        repeated_ids = [(value, count) for value, count in id_counts.items() if count > 1]
        print(f"\nIdentifiants (id_mutation) répétés : {len(repeated_ids)}")
        if repeated_ids:
            print(f"Top {min(top_n, len(repeated_ids))} identifiants :")
            for value, count in sorted(repeated_ids, key=lambda item: item[1], reverse=True)[:top_n]:
                print(f"  - {value}: {count} occurrences")
    else:
        print("\nColonne 'id_mutation' absente ou vide.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse rapide d'un fichier CSV (valeurs manquantes et doublons).")
    parser.add_argument("csv_path", type=Path, help="Chemin vers le fichier CSV à analyser")
    parser.add_argument("--top", type=int, default=5, help="Nombre d'éléments à afficher pour les listes (par défaut 5)")
    args = parser.parse_args()

    analyse_csv(args.csv_path, args.top)


if __name__ == "__main__":
    main()
