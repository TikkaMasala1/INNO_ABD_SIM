from mesa.batchrunner import batch_run
from model import TrafficModel
import pandas as pd

params = {
    "width": 20,
    "height": 20,
    "num_lanes": 1,
    "car_spawn_rate": [5, 10, 15, 20, 25, 30, 35, 40],
    "car_speed": [1, 2, 3, 4, 5, 6, 7, 8],
    "light_strategy": ["auction", "fixed_cycle"]
}

results = batch_run(
    model_cls=TrafficModel,
    parameters=params,
    iterations=30,             # aantal runs per combinatie
    max_steps=500,             # hoe lang de sim loopt
    data_collection_period=1,  # hoe vaak je data verzamelt (bijv. elke stap)
    display_progress=True
)

df = pd.DataFrame(results)
df.to_csv("batch_results.csv", index=False)
print("Resultaten opgeslagen als batch_results.csv")