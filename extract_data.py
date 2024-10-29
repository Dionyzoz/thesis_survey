import pandas as pd

from sqlalchemy import create_engine

engine = create_engine("sqlite:///respondents.db")


study1 = pd.read_sql_table("study1", con=engine)

study2 = pd.read_sql_table("study2", con=engine)


religiosity = {
    "Very religious": 4,
    "Moderately religious": 3,
    "Slightly religious": 2,
    "Not religious": 1,
}


study1.dropna(subset=["tdg_allocation"], inplace=True)

study2.dropna(subset=["tdg_allocation"], inplace=True)

study1["religiosity"] = study1["religiosity"].replace(religiosity)

study2["religiosity"] = study2["religiosity"].replace(religiosity)


study1["game_completed"] = study1["unique_key"].notna()

study2["game_completed"] = study2["unique_key"].notna()


study1 = study1[
    [
        "control_question",
        "religiosity",
        "gender",
        "country",
        "race",
        "age",
        "marital_status",
        "has_children",
        "game_completed",
        "tdg_allocation",
        "mass",
        "student",
    ]
]

study2 = study2[
    [
        "comparison",
        "compare_with_top",
        "religiosity",
        "gender",
        "country",
        "race",
        "age",
        "marital_status",
        "has_children",
        "game_completed",
        "tdg_allocation",
        "mass",
        "student",
    ]
]

study1 = study1.applymap(
    lambda x: x.replace("\u2019", "'") if isinstance(x, str) else x
)
study1 = study1.applymap(
    lambda x: x.encode("ascii", "ignore").decode("ascii") if isinstance(x, str) else x
)


study2 = study2.applymap(
    lambda x: x.replace("\u2019", "'") if isinstance(x, str) else x
)
study2 = study2.applymap(
    lambda x: x.encode("ascii", "ignore").decode("ascii") if isinstance(x, str) else x
)

print(study1)
print(study2)
study1.to_stata("study1.dta", version=117)
study2.to_stata("study2.dta", version=117)
