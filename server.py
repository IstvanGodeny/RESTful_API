import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, Boolean, Text

## Create the Flask app
app = Flask(__name__)


## Create Database
class Base(DeclarativeBase):
    pass

SQLALCHEMY_DB_URI = os.environ.get("DATABASE_URI")
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DB_URI
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 280}

db = SQLAlchemy(model_class=Base)
db.init_app(app)

## Create Table
# Init table
class Properties(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=True)
    number_of_floors: Mapped[int] = mapped_column(Integer, nullable=True)
    number_of_rooms: Mapped[int] = mapped_column(Integer, nullable=True)
    number_of_bathrooms: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(Text, nullable=True)
    parking_space: Mapped[bool] = mapped_column(Boolean, nullable=True)
    living_room: Mapped[bool] = mapped_column(Boolean, nullable=True)
    dining_room: Mapped[bool] = mapped_column(Boolean, nullable=True)
    garage: Mapped[bool] = mapped_column(Boolean, nullable=True)
    garden: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # Create dictionary from the database
    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)

        return dictionary

# Create table after init
with app.app_context():
    db.create_all()

# String to bool
def str_to_bool(value):
    if value.lower() == "true" or value.lower() == "t" or value.lower() == "1"  or value.lower() == "yes" or value.lower() == "y":
        return True
    elif value.lower() == "false" or value.lower() == "f" or value.lower() == "0"  or value.lower() == "no" or value.lower() == "n":
        return False
    else:
        return -1


## Routes
# Home
@app.route("/")
def home():
    return render_template('index.html')


# All data and filter option Route
@app.route("/get", methods=["GET"])
def all_and_filtered():
    if request.args:
        filters = []
        for query, value in request.args.items():
            query_key = getattr(Properties, query, None)
            if query == "number_of_floors" or query == "number_of_rooms" or query == "number_of_bathrooms":
                filters.append(query_key == int(value))
            elif query == "parking_space" or query == "living_room" or query == "dining_room" or query == "garage" or query == "garden":
                filters.append(query_key == str_to_bool(value))
            else:
                filters.append(query_key == value)

        result = db.session.execute(db.select(Properties).where(*filters))
        filtered_properties = result.scalars().all()
        if filtered_properties:
            return jsonify(properties=[house.to_dict() for house in filtered_properties])
        else:
            return jsonify(error={"Not found": "Sorry, we do not have a property with the condition."})
    else:
        result = db.session.execute(db.select(Properties).order_by(Properties.id))
        all_properties = result.scalars().all()
        return jsonify(properties=[house.to_dict() for house in all_properties])

# Add a data
@app.route("/post", methods=["POST"])
def add():
    if len(request.args) == 10:
        new_house_type = request.args.get("type", type=str)
        new_house_number_of_floors = request.args.get("number_of_floors", type=int)
        new_house_number_of_rooms = request.args.get("number_of_rooms", type=int)
        new_house_number_of_bathrooms = request.args.get("number_of_bathrooms", type=int)
        new_house_location = request.args.get("location", type=str)
        new_house_parking_space = str_to_bool(request.args.get("parking_space"))
        new_house_living_room = str_to_bool(request.args.get("living_room"))
        new_house_dining_room = str_to_bool(request.args.get("dining_room"))
        new_house_garage = str_to_bool(request.args.get("garage"))
        new_house_garden = str_to_bool(request.args.get("garden"))

        new_house = Properties(
            type = new_house_type,
            number_of_floors = new_house_number_of_floors,
            number_of_rooms = new_house_number_of_rooms,
            number_of_bathrooms = new_house_number_of_bathrooms,
            location = new_house_location,
            parking_space = new_house_parking_space,
            living_room = new_house_living_room,
            dining_room = new_house_dining_room,
            garage = new_house_garage,
            garden = new_house_garden,
        )

        db.session.add(new_house)
        db.session.commit()
        return jsonify(response={"success": "Successfully added the new house."})
    else:
        return jsonify(response={"error": "All details are required."})

# Update data, PATCH
@app.route("/patch", methods=["PATCH"])
def update():
    if request.args:
        if request.args.get("id"):
            try:
                property_to_update = db.get_or_404(Properties, request.args.get("id", type=int))
                for key, value in request.args.items():
                    if key == "number_of_floors" or key == "number_of_rooms" or key == "number_of_bathrooms":
                        if key == "number_of_floors":
                            property_to_update.number_of_floors = int(value)
                        elif key == "number_of_rooms":
                            property_to_update.number_of_rooms = int(value)
                        elif key == "number_of_bathrooms":
                            property_to_update.number_of_bathrooms = int(value)
                    elif key == "parking_space" or key == "living_room" or key == "dining_room" or key == "garage" or key == "garden":
                        if key == "parking_space":
                            property_to_update.parking_space = str_to_bool(value)
                        elif key == "living_room":
                            property_to_update.living_room = str_to_bool(value)
                        elif key == "dining_room":
                            property_to_update.dining_room = str_to_bool(value)
                        elif key == "garage":
                            property_to_update.garage = str_to_bool(value)
                        elif key == "garden":
                            property_to_update.garden = str_to_bool(value)
                    else:
                        if key == "location":
                            property_to_update.location = value
                        elif key == "type":
                            property_to_update.type = value
                    db.session.commit()
                return jsonify(response={"Success": "There is a property in the database and the details has been updated for the requested 'id'."})
            except:
                return jsonify(response={"error": "There is no property in the database with the requested 'id' or you entered an invalid value. Please check and try again."})
        else:
            return jsonify(response={"error": "The 'id' of the property is a mandatory fields."})
    else:
        return jsonify(response={"error": "The query list is empty."})

# Delete data DELETE
@app.route("/delete", methods=["DELETE"])
def delete():
    if request.args:
        if request.args.get("id"):
            try:
                property_to_delete = db.get_or_404(Properties, request.args.get("id", type=int))
                db.session.delete(property_to_delete)
                db.session.commit()
                return jsonify(response={"Success": "The property with the requested 'id' has been deleted."})
            except:
                return jsonify(response={"error": "There is no property in the database with the requested 'id'."})
        else:
            return jsonify(response={"error": "The 'id' of the property is the only and mandatory fields."})
    else:
        return jsonify(response={"error": "The query list is empty."})


## Run the server
if __name__ == "__main__":
    app.run()
