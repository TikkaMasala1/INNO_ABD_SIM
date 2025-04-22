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

iterations = 100
max_steps = 1000
data_collection_period = 1


output_filename = "combined_batch_results.csv"
output_filepath = output_filename # Save in the current directory

all_results_list = []

total_runs = len(light_strategies) * len(scenarios)
current_run = 0

for strategy in light_strategies:
    for scenario in scenarios:
        current_run += 1
        print(f"\n--- Starting Run {current_run}/{total_runs} ---")
        print(f"Light Strategy: {strategy}")
        print(f"Traffic Condition: {scenario['traffic_condition']}")
        print(f"Car Speed: {scenario['car_speed']}")

        # Combine base parameters with current scenario parameters
        params_for_run = {
            **base_params,
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

        # Add the results from this run to the main list
        all_results_list.extend(results)
        print(f"\nun {current_run}/{total_runs} complete. Results collected.")

print("\nAll batch runs finished. Combining results...")

# Create a single DataFrame from the list of all results
combined_df = pd.DataFrame(all_results_list)

# Save the combined DataFrame to a single CSV file
combined_df.to_csv(output_filepath, index=False)
print(f"All results saved to {output_filepath}")
