# OptiDech3.py

from flask import Flask, render_template, request, jsonify
import VRP_OSM
from VRP_OSM import create_data_model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    num_camions = int(request.form['num_camions'])
    camion_id = int(request.form['camion_id'])
    model = create_data_model() 
    model['num_camions'] = num_camions
    data = {
        'num_camions': num_camions,
        'camion_id': camion_id,
        'full_bins': model['full_bins']
    }
    results = VRP_OSM.run(data)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)

