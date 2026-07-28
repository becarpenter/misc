"""This program tests oslock. Run at least two copies simultaneously."""

import oslock
import time
import random
prng = random.SystemRandom() # best PRNG we can get
lock_count = 0
wait = 10
lock_loop = 10

while True:
    time.sleep(prng.randint(3,7))
    if oslock.get_lock(): 
        print("Got lock")
        lock_count = 0
        time.sleep(1) # busywork holding the lock
    else:
        print("No lock", lock_count)
        lock_count += 1     
        if lock_count < lock_loop:
            continue
        #We get here only if someone else is hogging the lock
        print("Somebody is blocking the lock")
        lock_count = 0
        continue

    if oslock.release_lock():
        print("Unlocked")
    else:
        print("Release failed  - already released?")
         
