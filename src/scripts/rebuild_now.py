import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main():
    from core.db import get_db_connection
    from core.config import GEMINI_API_KEY
    from core.consolidation import LogicIntelligence
    from storage.sqlite_api import sqlite_storage
    from storage.vector_store import vector_manager

    db = await get_db_connection()
    async with db.execute(
        "SELECT name, project, code, description, tags, language "
        "FROM logichive_functions "
        "WHERE embedding IS NULL OR embedding = '' OR embedding = '[]' OR embedding = 'null'"
    ) as cursor:
        rows = await cursor.fetchall()

    total = len(rows)
    print(f"\n{'=' * 60}")
    print(f"  rebuild_embeddings: {total} functions need embedding regeneration")
    print(f"{'=' * 60}\n")

    if total == 0:
        print("Nothing to do.")
        return

    intel = LogicIntelligence(GEMINI_API_KEY)
    semaphore = asyncio.Semaphore(3)
    success = 0
    fail = 0

    async def process_one(row):
        nonlocal success, fail
        name, proj, code, desc, tags_json, lang = row
        try:
            async with semaphore:
                tags = json.loads(tags_json) if tags_json else []
                search_doc = intel.construct_search_document(name, desc or "", tags, code or "")
                embedding = await intel.generate_embedding(search_doc)
                await sqlite_storage.update_function_embedding(name, proj, embedding)
                await vector_manager.upsert_vector(
                    name,
                    embedding,
                    metadata={"project": proj, "language": lang or "python"},
                    project=proj,
                )
                success += 1
                print(f"  [OK] {name} ({proj})")
        except Exception as e:
            fail += 1
            print(f"  [FAIL] {name} ({proj}): {e}")

    await asyncio.gather(*[process_one(row) for row in rows])

    print(f"\n{'=' * 60}")
    print(f"  Done: {success} succeeded, {fail} failed, {total} total")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
