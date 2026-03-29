#!/usr/bin/env python3
"""rwlock - Read-write lock with writer priority and fairness control."""
import sys, json, threading, time

class RWLock:
    def __init__(self, writer_priority=True):
        self._lock = threading.Lock()
        self._readers = 0
        self._writer = False
        self._read_ok = threading.Condition(self._lock)
        self._write_ok = threading.Condition(self._lock)
        self._waiting_writers = 0
        self._writer_priority = writer_priority
        self.stats = {"reads": 0, "writes": 0, "read_waits": 0, "write_waits": 0}

    def read_acquire(self):
        with self._lock:
            while self._writer or (self._writer_priority and self._waiting_writers > 0):
                self.stats["read_waits"] += 1
                self._read_ok.wait()
            self._readers += 1
            self.stats["reads"] += 1

    def read_release(self):
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_ok.notify()

    def write_acquire(self):
        with self._lock:
            self._waiting_writers += 1
            while self._writer or self._readers > 0:
                self.stats["write_waits"] += 1
                self._write_ok.wait()
            self._waiting_writers -= 1
            self._writer = True
            self.stats["writes"] += 1

    def write_release(self):
        with self._lock:
            self._writer = False
            self._read_ok.notify_all()
            self._write_ok.notify()

def main():
    lock = RWLock()
    results = []
    def reader(rid):
        lock.read_acquire()
        results.append(f"R{rid}+")
        time.sleep(0.01)
        results.append(f"R{rid}-")
        lock.read_release()
    def writer(wid):
        lock.write_acquire()
        results.append(f"W{wid}+")
        time.sleep(0.02)
        results.append(f"W{wid}-")
        lock.write_release()
    threads = []
    for i in range(4): threads.append(threading.Thread(target=reader, args=(i,)))
    for i in range(2): threads.append(threading.Thread(target=writer, args=(i,)))
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"Order: {' '.join(results)}")
    print(json.dumps(lock.stats, indent=2))

if __name__ == "__main__":
    main()
