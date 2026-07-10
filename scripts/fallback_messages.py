#!/usr/bin/env python3
"""100 custom fallback messages for the split-flap board."""

FALLBACK_MESSAGES = [
    # Status & shipping vibes
    ["STILL SHIPPING", "STILL DEBUGGING"],
    ["CODE COMPILES", "COFFEE PENDING"],
    ["PUSH TO PROD", "PRAY TO GOD"],
    ["FEATURE LOCKED", "BUG UNLOCKED"],
    ["MERGE CONFLICTS", "LIFE CONFLICTS"],
    ["GIT BLAME", "SELF BLAME"],
    ["TESTING 123", "STILL BROKEN"],
    ["SHIPPED IT", "REGRET IT"],
    
    # Weather & vibes (your persona)
    ["BANGKOK HEAT", "KEYBOARD SWEAT"],
    ["RAIN RADAR ON", "CODE FLOWING"],
    ["STORM WARNING", "BUG WARNING"],
    ["CLEAR SKIES", "CLEAR MIND"],
    ["HUMIDITY HIGH", "PATIENCE LOW"],
    ["PARTLY CLOUDY", "MOSTLY TIRED"],
    
    # Project status
    ["SOL ALIVE", "LOCAL LLM HOT"],
    ["BLOOD AI", "13K LINES DEEP"],
    ["SUMO ROBOT", "127.0.0.1:67"],
    ["SUMO WINS", "CODE WINS"],
    ["AUTONOMOUS", "ANXIOUS"],
    ["REFACTOR MODE", "ON FIRE MODE"],
    ["PLUGIN ARCH", "60 PERCENT THERE"],
    
    # Dev mood
    ["COFFEE FUEL", "CODE RULE"],
    ["BREAKING THINGS", "FIXING THINGS"],
    ["CLEAN COMPILES", "DIRTY MIND"],
    ["NO MERGE CONFLICTS", "YES LIFE CONFLICTS"],
    ["STABLE BUILD", "UNSTABLE MOOD"],
    ["TESTS PASSING", "SANITY PASSING"],
    ["REFACTOR DAY", "REGRET DAY"],
    ["SHIP IT", "SKIP IT"],
    
    # Music & mood (MF DOOM / Radiohead / Chopin)
    ["MF DOOM", "DEAD SERIOUS"],
    ["RADIOHEAD", "ROBOT HEAD"],
    ["CHOPIN", "CODE ON"],
    ["PARANOID ANDROID", "PARANOID DEV"],
    ["NO SURPRISES", "MANY BUGS"],
    ["ALL CAPS", "ALL BUGS"],
    
    # Dry humor
    ["THE BORING SOLUTION", "ALWAYS WORKS"],
    ["SIMPLICITY WINS", "COMPLEXITY LOSES"],
    ["SOLUTION = BORING", "WORKS = TRUE"],
    ["LESS IS MORE", "MORE IS BROKEN"],
    ["KISS: KEEP IT SIMPLE", "STUPID BUGS"],
    ["DO ONE THING", "DO IT RIGHT"],
    
    # Technical inside jokes
    ["PRODUCTION", "IS PRODUCTION"],
    ["YOLO DEPLOY", "YOLO ROLLBACK"],
    ["IT WORKS", "DONT TOUCH IT"],
    ["WORKS ON MY MACHINE", "BREAKS ON PROD"],
    ["LOCALHOST", "BESTHOST"],
    ["SYNTAX ERROR", "LIFE ERROR"],
    ["STACK OVERFLOW", "MENTAL OVERFLOW"],
    ["CTRL ALT DELETE", "LIFE"],
    
    # Time-based vibes
    ["2AM CODING", "3AM REGRETTING"],
    ["MORNING COFFEE", "EVENING CHAOS"],
    ["WEEKEND PROJECT", "WEEK CONSUMED"],
    ["PROCRASTINATING", "SHIPPING ANYWAY"],
    ["DEADLINE TOMORROW", "PANIC TODAY"],
    ["TIME MOVES WEIRD", "CODE MOVES WEIRD"],
    
    # Existential dev thoughts
    ["WHY DO I CODE", "PASSION OR PAIN"],
    ["FRONTEND FINE", "BACKEND CRYING"],
    ["API WORKING", "DOCS MISSING"],
    ["IT COMPILES", "DOES IT WORK THO"],
    ["WORKS SOMETIMES", "BREAKS ALWAYS"],
    ["IF IT WORKS", "DONT ASK WHY"],
    ["NEVER TOUCH THAT", "LEGACY CODE LIVES"],
    
    # Quick one-liners
    ["SLEEP IS FOR QUITTERS"],
    ["COFFEE > SLEEP"],
    ["BUG HUNTER MODE ON"],
    ["FEATURE INCOMING"],
    ["OPTIMIZING VIBES"],
    ["VELOCITY ENGAGED"],
    ["DEPLOYMENT LOCKED"],
    ["PATCH INCOMING"],
    ["LIVE EDGE TESTING"],
    ["PUSHING BOUNDARIES"],
    
    # Bangkok / Thailand flavor
    ["BANGKOK DEV", "WEATHER NERD"],
    ["THAI KEYBOARD", "FAST FINGERS"],
    ["SATAY AND CODING", "PERFECT COMBO"],
    ["TROPICAL CODING", "ISLAND VIBES"],
    ["BANGKOK TRAFFIC", "CODE TRAFFIC"],
    
    # Sarcasm & wit
    ["WORKS PERFECTLY", "NEVER BREAKS"],
    ["DEFINITELY STABLE", "PROBABLY BROKEN"],
    ["NOT A BUG", "FEATURE REQUEST"],
    ["FRONTEND EASY", "BACKEND HELL"],
    ["AGILE PROCESS", "CHAOS MANAGEMENT"],
    ["TECHNICAL DEBT", "STUDENT LOANS"],
    ["LEGACY CODE", "HAUNTED CODE"],
    
    # Poetic dev vibes
    ["ELEGANCE IN CODE"],
    ["BEAUTY IN SIMPLICITY"],
    ["POETRY IN LOGIC"],
    ["MACHINES THINK", "HUMANS PRAY"],
    ["BITS AND BYTES", "HEART AND SOUL"],
]

if __name__ == "__main__":
    print(f"Total fallback messages: {len(FALLBACK_MESSAGES)}\n")
    for i, msg in enumerate(FALLBACK_MESSAGES, 1):
        print(f"{i:3d}. {' / '.join(msg)}")
