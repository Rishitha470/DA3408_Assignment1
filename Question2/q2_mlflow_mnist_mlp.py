"""
Q2 
  - Hyperparameters varied: learning_rate, batch_size (6 runs)
 
"""

import mlflow
import mlflow.sklearn
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, log_loss

# ---------------------------------------------------------------------------
# Step 0 — Setup 
# ---------------------------------------------------------------------------
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("mnist-mlp-classifier")
print("Tracking URI:", mlflow.get_tracking_uri())

# ---------------------------------------------------------------------------
# Step 1 — Load MNIST instead of IRIS
# 
# ---------------------------------------------------------------------------
print("Downloading MNIST ")
mnist = fetch_openml("mnist_784", version=1, as_frame=False)
X = mnist.data / 255.0            # scale pixels 0-1, MLPs train much better this way
y = mnist.target.astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train size: {X_train.shape[0]}   Test size: {X_test.shape[0]}")


def train_and_evaluate(learning_rate=0.001, batch_size=32,
                        hidden_layer_sizes=(100,), n_epochs=15):
    """
    Same role as the starter's train_and_evaluate(), but:
      - uses MLPClassifier instead of RandomForestClassifier
      - trains epoch-by-epoch (warm_start=True) so we can log a metric
        PER EPOCH instead of just one final number
    Returns the fitted model plus per-epoch history lists.
    """
    model = MLPClassifier(
        hidden_layer_sizes=hidden_layer_sizes,
        learning_rate_init=learning_rate,
        batch_size=batch_size,
        max_iter=1,          
        warm_start=True,    
        random_state=42,
    )

    train_loss_history = []
    val_acc_history = []

    for epoch in range(n_epochs):
        model.fit(X_train, y_train)
        train_loss = log_loss(y_train, model.predict_proba(X_train))
        val_acc = accuracy_score(y_test, model.predict(X_test))
        train_loss_history.append(train_loss)
        val_acc_history.append(val_acc)

    return model, train_loss_history, val_acc_history


# ---------------------------------------------------------------------------
# Step 2 & 3 — Instrument it: manual logging
# ---------------------------------------------------------------------------
def train_and_log(learning_rate=0.001, batch_size=32,
                   hidden_layer_sizes=(100,), n_epochs=15, run_name=None):
    with mlflow.start_run(run_name=run_name):
       
        mlflow.log_param("model_type", "MLPClassifier")
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("hidden_layer_sizes", hidden_layer_sizes)
        mlflow.log_param("n_epochs", n_epochs)

        model, train_loss_history, val_acc_history = train_and_evaluate(
            learning_rate, batch_size, hidden_layer_sizes, n_epochs
        )

        # --- metrics, logged ONE PER EPOCH (the "mlflow.log_metric" lines for part 3) ---
        for epoch in range(n_epochs):
            mlflow.log_metric("train_loss", train_loss_history[epoch], step=epoch)
            mlflow.log_metric("val_accuracy", val_acc_history[epoch], step=epoch)

        mlflow.set_tag("team", "data-science")
        mlflow.sklearn.log_model(model, name="model")

        run_id = mlflow.active_run().info.run_id
        final_acc = val_acc_history[-1]
        final_loss = train_loss_history[-1]
        print(f"Logged run {run_id}  |  lr={learning_rate}  bs={batch_size}  "
              f"final_val_acc={final_acc:.4f}  final_train_loss={final_loss:.4f}")
        return run_id


# ---------------------------------------------------------------------------
# Step 4 — Sweep: 6 runs varying learning_rate AND batch_size
# ---------------------------------------------------------------------------
configs = [
    (0.001, 32),
    (0.001, 128),
    (0.001, 512),
    (0.01,  32),
    (0.01,  128),
    (0.01,  512),
]

sweep_run_ids = []
for lr, bs in configs:
    rid = train_and_log(
        learning_rate=lr, batch_size=bs,
        run_name=f"mlp-lr{lr}-bs{bs}",
    )
    sweep_run_ids.append(rid)

print("\nSweep run IDs:", sweep_run_ids)

# ---------------------------------------------------------------------------
# Step 5 — Find the best run with mlflow.search_runs()
# ---------------------------------------------------------------------------
runs_df = mlflow.search_runs(
    experiment_names=["mnist-mlp-classifier"],
    order_by=["metrics.val_accuracy DESC"],
)

display_cols = [c for c in runs_df.columns if c in (
    "run_id", "tags.mlflow.runName", "params.learning_rate",
    "params.batch_size", "metrics.val_accuracy", "metrics.train_loss",
)]
print("\nAll runs, sorted by val_accuracy:")
print(runs_df[display_cols].to_string(index=False))

best_run = runs_df.iloc[0]
print(f"\nBest run: {best_run['run_id']}  "
      f"(val_accuracy={best_run['metrics.val_accuracy']:.4f})")

print("\nDone. Now open http://localhost:5000 in your browser to screenshot the comparison table.")
