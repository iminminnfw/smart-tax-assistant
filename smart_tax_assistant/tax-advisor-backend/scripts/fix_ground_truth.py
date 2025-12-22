"""
Script to fix ground truth tax_saving values based on correct marginal rates
"""

# Test Case 1: 600K income, marginal rate 10%
tc1_updates = {
    "plan_1": {"total": 6000, "allocations": [2000, 3000, 1000]},
    "plan_2": {"total": 10000, "allocations": [6000, 3000, 1000]},
    "plan_3": {"total": 15000, "allocations": [9000, 3000, 2000]}
}

# Test Case 2: 1.5M income, marginal rate 15%
tc2_updates = {
    "plan_1": {"total": 45000, "allocations": [45000, 24000, 6000]},
    "plan_2": {"total": 75000, "allocations": [75000, 37500, 12500]},
    "plan_3": {"total": 120000, "allocations": [120000, 48000, 24000, 12000]}
}

# Test Case 3: 360K income, marginal rate 5%
tc3_updates = {
    "plan_1": {"total": 2000, "allocations": [1000, 500, 500]},
    "plan_2": {"total": 3000, "allocations": [1500, 900, 600]},
    "plan_3": {"total": 4000, "allocations": [2000, 1200, 800]}
}

print("Ground Truth Tax Saving Corrections:")
print("\nTest Case 1 (600K, 10% marginal):")
for plan, values in tc1_updates.items():
    print(f"  {plan}: total={values['total']:,}, allocations={values['allocations']}")

print("\nTest Case 2 (1.5M, 15% marginal):")
for plan, values in tc2_updates.items():
    print(f"  {plan}: total={values['total']:,}, allocations={values['allocations']}")

print("\nTest Case 3 (360K, 5% marginal):")
for plan, values in tc3_updates.items():
    print(f"  {plan}: total={values['total']:,}, allocations={values['allocations']}")
