from mesa.batchrunner import batch_run
from model import TrafficModel
import pandas as pd
import os
# Fixed Parameters
base_params = {
    "width": 20,
    "height": 20,
    "num_lanes": 1,
}

# Parameters for the Specific Scenarios
light_strategies = ["auction", "fixed_cycle", "dutch_system"]
scenarios = [
    {"traffic_condition": "Normale tijd", "car_speed": 2},
    {"traffic_condition": "Spitsuur", "car_speed": 2},
    {"traffic_condition": "Normale tijd", "car_speed": 5},
    {"traffic_condition": "Spitsuur", "car_speed": 5},
]

# Batch Run Settings
iterations = 30
max_steps = 500
data_collection_period = 1

output_dir = "batch_run_results"
os.makedirs(output_dir, exist_ok=True) # Create the directory if it doesn't exist

# Loop through each combination and run separately
total_runs = len(light_strategies) * len(scenarios)
current_run = 0

for strategy in light_strategies:
    for scenario in scenarios:
        current_run += 1
        print(f"\nStarting Run {current_run}/{total_runs} ---")
        print(f"Light Strategy: {strategy}")
        print(f"Traffic Condition: {scenario['traffic_condition']}")
        print(f"Car Speed: {scenario['car_speed']}")

        params_for_run = {
            **base_params, # Unpack base parameters
            "light_strategy": strategy,
            "traffic_condition": scenario["traffic_condition"],
            "car_speed": scenario["car_speed"]
        }

        results = batch_run(
            model_cls=TrafficModel,
            parameters=params_for_run,
            iterations=iterations,
            max_steps=max_steps,
            data_collection_period=data_collection_period,
            display_progress=True
        )

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        # Replace spaces in traffic condition with underscores for cleaner filenames
        tc_filename = scenario['traffic_condition'].replace(" ", "_")
        filename = f"{strategy}_{tc_filename}_speed_{scenario['car_speed']}.csv"
        filepath = os.path.join(output_dir, filename) # Save inside the directory

        # Save DataFrame to CSV
        df.to_csv(filepath, index=False)
        print(f"\nRun complete. Results saved to {filepath}")

print("\nAll batch runs finished. ---")