from mesa.batchrunner import batch_run
from model import TrafficModel
import pandas as pd

params = {
    "width": 20,
    "height": 20,
    "num_lanes": 1,
    "traffic_condition": ["Normale tijd", "Spitsuur"],
    "car_speed": [1, 2, 3, 4, 5, 6, 7, 8],
    "light_strategy": ["auction", "fixed_cycle", "dutch_system"]
}

results = batch_run(
    model_cls=TrafficModel,
    parameters=params,
    iterations=30,
    max_steps=500,
    data_collection_period=1,
    display_progress=True
)

df = pd.DataFrame(results)
df.to_csv("batch_results.csv", index=False)
print("Resultaten opgeslagen als batch_results.csv")