#!/usr/bin/env python3
"""rwlock - Read-write lock implementation with writer priority."""
import sys, threading, time

class RWLock:
    def __init__(self):
        self.readers = 0
        self.writer = False
        self.write_waiters = 0
        self._lock = threading.Lock()
        self._read_ok = threading.Condition(self._lock)
        self._write_ok = threading.Condition(self._lock)

    def acquire_read(self):
        with self._read_ok:
            while self.writer or self.write_waiters > 0:
                self._read_ok.wait()
            self.readers += 1

    def release_read(self):
        with self._lock:
            self.readers -= 1
            if self.readers == 0:
                self._write_ok.notify()

    def acquire_write(self):
        with self._write_ok:
            self.write_waiters += 1
            while self.writer or self.readers > 0:
                self._write_ok.wait()
            self.write_waiters -= 1
            self.writer = True

    def release_write(self):
        with self._lock:
            self.writer = False
            self._write_ok.notify()
            self._read_ok.notify_all()

def test():
    lock = RWLock()
    results = []
    def reader(n):
        lock.acquire_read()
        results.append(f"r{n}_start")
        time.sleep(0.01)
        results.append(f"r{n}_end")
        lock.release_read()
    def writer(n):
        lock.acquire_write()
        results.append(f"w{n}_start")
        time.sleep(0.01)
        results.append(f"w{n}_end")
        lock.release_write()
    t1 = threading.Thread(target=reader, args=(1,))
    t2 = threading.Thread(target=reader, args=(2,))
    t3 = threading.Thread(target=writer, args=(1,))
    t1.start(); t2.start()
    time.sleep(0.005)
    t3.start()
    t1.join(); t2.join(); t3.join()
    assert "r1_start" in results
    assert "w1_start" in results
    assert "w1_end" in results
    lock2 = RWLock()
    lock2.acquire_write()
    lock2.release_write()
    lock2.acquire_read()
    lock2.release_read()
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("rwlock: Read-write lock. Use --test")
