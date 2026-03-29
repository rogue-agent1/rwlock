#!/usr/bin/env python3
"""rwlock: Read-write lock (multiple readers, exclusive writer)."""
import threading, sys, time

class RWLock:
    def __init__(self):
        self._readers = 0
        self._lock = threading.Lock()
        self._read_ok = threading.Condition(self._lock)
        self._write_ok = threading.Condition(self._lock)
        self._writing = False
        self._write_waiting = 0

    def read_acquire(self):
        with self._lock:
            while self._writing or self._write_waiting > 0:
                self._read_ok.wait()
            self._readers += 1

    def read_release(self):
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_ok.notify_all()

    def write_acquire(self):
        with self._lock:
            self._write_waiting += 1
            while self._writing or self._readers > 0:
                self._write_ok.wait()
            self._write_waiting -= 1
            self._writing = True

    def write_release(self):
        with self._lock:
            self._writing = False
            self._read_ok.notify_all()
            self._write_ok.notify_all()

def test():
    rw = RWLock()
    data = [0]
    log = []
    lock = threading.Lock()

    def reader(n):
        rw.read_acquire()
        val = data[0]
        time.sleep(0.02)
        with lock:
            log.append(("read", n, val))
        rw.read_release()

    def writer(n, val):
        rw.write_acquire()
        data[0] = val
        time.sleep(0.02)
        with lock:
            log.append(("write", n, val))
        rw.write_release()

    # Multiple concurrent readers
    threads = [threading.Thread(target=reader, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    with lock:
        reads = [e for e in log if e[0] == "read"]
    assert len(reads) == 5

    # Writer exclusivity
    log.clear()
    t1 = threading.Thread(target=writer, args=(1, 42))
    t2 = threading.Thread(target=reader, args=(10,))
    t1.start()
    time.sleep(0.005)
    t2.start()
    t1.join()
    t2.join()
    with lock:
        write_idx = next(i for i, e in enumerate(log) if e[0] == "write")
        read_idx = next(i for i, e in enumerate(log) if e[0] == "read")
    assert write_idx < read_idx  # Writer completes before reader
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: rwlock.py test")
