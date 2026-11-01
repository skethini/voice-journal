import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import { api } from "./client";

interface QueueDB extends DBSchema {
  pending: {
    key: number;
    value: {
      blob: Blob;
      duration_s: number;
      createdAt: number;
    };
  };
}

let dbPromise: Promise<IDBPDatabase<QueueDB>> | null = null;

function getDb() {
  if (!dbPromise) {
    dbPromise = openDB<QueueDB>("voice-journal", 1, {
      upgrade(db) {
        db.createObjectStore("pending", { keyPath: "id", autoIncrement: true });
      },
    });
  }
  return dbPromise;
}

export async function enqueueUpload(blob: Blob, duration_s: number) {
  const db = await getDb();
  await db.add("pending", { blob, duration_s, createdAt: Date.now() });
  await flushQueue();
}

export async function flushQueue() {
  const db = await getDb();
  const keys = await db.getAllKeys("pending");
  for (const key of keys) {
    const item = await db.get("pending", key);
    if (!item) continue;
    try {
      await api.createEntry(item.blob, item.duration_s);
      await db.delete("pending", key);
    } catch {
      break;
    }
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => {
    void flushQueue();
  });
}
