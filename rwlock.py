#!/usr/bin/env python3
"""Read-write lock implementation."""
import threading, time

class RWLock:
    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0
        self._writers = 0
        self._write_waiting = 0

    def acquire_read(self):
        with self._read_ready:
            while self._writers > 0 or self._write_waiting > 0:
                self._read_ready.wait()
            self._readers += 1

    def release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        with self._read_ready:
            self._write_waiting += 1
            while self._readers > 0 or self._writers > 0:
                self._read_ready.wait()
            self._write_waiting -= 1
            self._writers += 1

    def release_write(self):
        with self._read_ready:
            self._writers -= 1
            self._read_ready.notify_all()

class ReadContext:
    def __init__(self, lock): self.lock = lock
    def __enter__(self): self.lock.acquire_read(); return self
    def __exit__(self, *a): self.lock.release_read()

class WriteContext:
    def __init__(self, lock): self.lock = lock
    def __enter__(self): self.lock.acquire_write(); return self
    def __exit__(self, *a): self.lock.release_write()

def test():
    lock = RWLock()
    data = [0]
    errors = []
    def reader(results, idx):
        with ReadContext(lock):
            results[idx] = data[0]
            time.sleep(0.01)
    def writer(val):
        with WriteContext(lock):
            data[0] = val
            time.sleep(0.01)
    # Concurrent reads
    results = [None] * 5
    threads = [threading.Thread(target=reader, args=(results, i)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert all(r == 0 for r in results)
    # Write then read
    writer(42)
    results2 = [None]
    reader(results2, 0)
    assert results2[0] == 42
    print("  rwlock: ALL TESTS PASSED")

if __name__ == "__main__":
    test()
