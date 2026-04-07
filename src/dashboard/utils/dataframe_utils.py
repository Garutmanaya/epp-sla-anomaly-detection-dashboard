import pandas as pd

from shared.data_dictionary import KEY_COLUMNS, NORMAL_STATUS, REQUIRED_INPUT_COLUMNS


def load_uploaded_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    missing = [column for column in REQUIRED_INPUT_COLUMNS if column not in df.columns]
    if missing:
        missing_csv = ", ".join(missing)
        raise ValueError(f"CSV is missing required columns: {missing_csv}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
    return df


def build_inference_payload(df: pd.DataFrame, models: list[str]) -> dict:
    df_copy = df.copy()
    for column in df_copy.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df_copy[column] = df_copy[column].astype(str)

    return {
        "models": models,
        "data": df_copy.to_dict(orient="records"),
    }


def build_status_comparison_table(results_by_model: dict[str, pd.DataFrame], models: list[str]) -> pd.DataFrame:
    merged = None

    for model in models:
        current = results_by_model[model][["Timestamp", "Command", "Status"]].copy()
        current.columns = [*KEY_COLUMNS, model]

        if merged is None:
            merged = current
        else:
            merged = merged.merge(current, on=KEY_COLUMNS, how="outer")

    merged["Agreement"] = merged[models].fillna("Missing").nunique(axis=1) == 1
    return merged.sort_values(KEY_COLUMNS).reset_index(drop=True)


def add_alert_flags(status_table: pd.DataFrame, models: list[str]) -> tuple[pd.DataFrame, list[str]]:
    alert_columns = []

    for model in models:
        alert_column = f"{model}_alert"
        status_table[alert_column] = status_table[model].fillna("Missing") != NORMAL_STATUS
        alert_columns.append(alert_column)

    return status_table, alert_columns
