import logging
from sqlalchemy import (
    Boolean,
    ForeignKey,
    create_engine,
    Column,
    Integer,
    String,
    Enum,
    Double,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, sessionmaker
import random
import secrets
from sqlalchemy.sql import column

# Define the database connection string
DATABASE_URL = "sqlite:///respondents.db"
TOTAL_TASK_TIME = 120
# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative class definitions
Base = declarative_base()


# Define enumerations for religiosity, gender, and race
religiosity = [
    "Very religious",
    "Moderately religious",
    "Slightly religious",
    "Not religious",
]


gender = ["Male", "Female", "Non-binary", "Prefer not to say"]

race = [
    "White",
    "Black or African American",
    "Asian",
    "Hispanic or Latino",
    "Native American",
    "Other",
]

marital_status_options = [
    "Single",
    "Married",
    "In a domestic partnership",
    "Divorced",
    "Widowed",
    "Prefer not to say",
]

has_children_options = ["Yes", "No", "Prefer not to say"]


# Define the Respondent class which maps to the respondents table
class Respondent:
    id = Column(Integer, primary_key=True, autoincrement=True)

    religiosity = Column(Integer, nullable=False)

    gender = Column(Enum(*gender), nullable=False)

    country = Column(String, nullable=False)

    race = Column(Enum(*race), nullable=False)

    age = Column(Integer, nullable=False)

    marital_status = Column(Enum(*marital_status_options), nullable=False)

    student = Column(Boolean, nullable=False)

    has_children = Column(Enum(*has_children_options), nullable=False)

    tdg_allocation = Column(Double)

    mass = Column(Integer)

    unique_key = Column(String)


class Study2_Respondent(Respondent, Base):
    __tablename__ = "study2"

    comparison = Column(String)
    compare_with_top = Column(Boolean)  # compares with bottom otherwise


class Study1_Respondent(Respondent, Base):
    __tablename__ = "study1"

    control_question = Column(String)


class LastAllocation(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, default=0)


# Create the respondents table
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)


s = Session()
last_allocation = s.query(LastAllocation).first()
if not last_allocation:
    config = LastAllocation(value=0)
    s.add(config)

    s.commit()

s.close()


def get_respondent(session, study, id) -> Respondent:
    if study == 1:
        return session.query(Study1_Respondent).filter_by(id=id).one()

    if study == 2:
        return session.query(Study2_Respondent).filter_by(id=id).one()


def handle_control_or_treamtent(study, id, form):
    session = Session()
    respondent: Respondent = get_respondent(session, study, id)
    if study == 1:
        respondent.control_question = form["control_question"]

    elif study == 2:
        respondent.comparison = form["interaction_reflection"]

    respondent.mass = form["ladder_position"]
    session.commit()


def post_allocation(study, id, allocation):
    session = Session()
    respondent = get_respondent(session, study, id)

    last_allocation = session.query(LastAllocation).with_for_update().first()
    allocated_to = last_allocation.value

    assert allocation <= 100 and allocation >= 0

    last_allocation.value = allocation  # how much you allocate to next

    respondent.tdg_allocation = allocation

    session.commit()

    return round(
        (allocated_to / 100) * TOTAL_TASK_TIME
        + (1 - (allocation / 100)) * TOTAL_TASK_TIME
    )


def randomize_study(request):
    form = request.form
    session = Session()
    compare_with_top = None

    completed_study1 = len(
        session.query(Study1_Respondent)
        .filter(column("tdg_allocation").isnot(None))
        .all()
    )

    completed_study2 = len(
        session.query(Study2_Respondent)
        .filter(column("tdg_allocation").isnot(None))
        .all()
    )

    respondent_d = {
        "religiosity": int(form["religiosity"]),
        "gender": form["gender"],
        "country": form["country"],
        "race": form["race"],
        "age": form["age"],
        "marital_status": form["marital_status"],
        "student": (form.get("employment_status") == "Student"),
        "has_children": form["has_children"],
    }

    if completed_study1 < completed_study2:
        study = 1

    elif completed_study2 < completed_study1:
        study = 2

    else:
        study = random.choice([1, 2])

    if study == 1:
        respondent = Study1_Respondent(**respondent_d)
        session.add(respondent)

    if study == 2:
        completed_study2 = (
            session.query(Study2_Respondent)
            .filter(column("tdg_allocation").isnot(None))
            .all()
        )

        compared_with_top = len(
            list(filter(lambda res: res.compare_with_top, completed_study2))
        )
        compared_with_bottom = len(
            list(filter(lambda res: not res.compare_with_top, completed_study2))
        )
        if compared_with_bottom < compared_with_top:
            compare_with_top = False

        elif compared_with_top < compared_with_bottom:
            compare_with_top = True

        else:
            compare_with_top = random.choice([True, False])

        respondent = Study2_Respondent(
            **respondent_d, compare_with_top=compare_with_top
        )
        session.add(respondent)

    session.commit()

    return {"study": study, "respondent_id": respondent.id} | (
        {"bottom": not compare_with_top} if study == 2 else {}
    )


def get_unique_key(study, respondent_id):
    session = Session()
    respondent = get_respondent(session, study, respondent_id)

    if respondent.unique_key:
        key = respondent.unique_key

    else:
        key = secrets.token_urlsafe(16)
        respondent.unique_key = key
        session.commit()

    return key
