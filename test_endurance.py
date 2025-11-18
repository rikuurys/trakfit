"""
Quick test to verify endurance decimal computation
"""

# Test data
test_cases = [
    (9, 30, 9.5),   # 9 minutes 30 seconds = 9.5
    (10, 0, 10.0),  # 10 minutes 0 seconds = 10.0
    (8, 45, 8.75),  # 8 minutes 45 seconds = 8.75
    (15, 15, 15.25), # 15 minutes 15 seconds = 15.25
]

def endurance_decimal(mins, secs):
    """Convert minutes and seconds to decimal minutes"""
    return float(mins) + (float(secs) / 60.0)

print("Testing endurance decimal conversion:")
print("-" * 50)

for mins, secs, expected in test_cases:
    result = endurance_decimal(mins, secs)
    status = "✓" if abs(result - expected) < 0.01 else "✗"
    print(f"{status} {mins}:{secs:02d} -> {result:.2f} (expected {expected:.2f})")

print("\nConversion back to mm:ss format:")
print("-" * 50)

for mins, secs, decimal in test_cases:
    # Convert back
    minutes = int(decimal)
    seconds = round((decimal - minutes) * 60)
    print(f"  {decimal:.2f} min -> {minutes}:{seconds:02d}")
