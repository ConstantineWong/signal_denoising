from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import os
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime
import io
import math
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

UPLOAD_FOLDER = 'asset'
OUTPUT_FOLDER = 'output'
RAW_IMG_FOLDER = 'raw_img'
ALLOWED_EXTENSIONS = {'csv'}
RECORDS_PER_PAGE = 20

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['RAW_IMG_FOLDER'] = RAW_IMG_FOLDER

# Add template context processor
@app.context_processor
def utility_processor():
    return dict(max=max, min=min)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_list():
    try:
        # Read the CSV file
        csv_path = os.path.join(os.path.dirname(__file__), 'check_list.csv')
        logger.debug(f"Reading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        return df['ecg'].tolist()
    except Exception as e:
        logger.error(f"Error in get_image_list: {str(e)}")
        return []

def update_csv_status(filename):
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'check_list.csv')
        logger.debug(f"Updating CSV status for file: {filename}")
        df = pd.read_csv(csv_path)
        
        # Update status and add timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[df['ecg'] == filename, 'Status'] = 'FINISHED'
        df.loc[df['ecg'] == filename, 'Time'] = current_time
        
        # Save back to CSV
        df.to_csv(csv_path, index=False)
        logger.debug("CSV status updated successfully")
    except Exception as e:
        logger.error(f"Error in update_csv_status: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def list_page():
    try:
        page = request.args.get('page', 1, type=int)
        logger.debug(f"Current page requested: {page}")
        
        if page < 1:
            page = 1
            logger.debug("Page number adjusted to 1")
            
        csv_path = os.path.join(os.path.dirname(__file__), 'check_list.csv')
        logger.debug(f"Reading CSV from: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at: {csv_path}")
            return render_template('list.html', 
                                 data=[],
                                 current_page=1,
                                 total_pages=1)
        
        df = pd.read_csv(csv_path)
        logger.debug(f"Total records in CSV: {len(df)}")
        
        # Calculate pagination
        total_records = len(df)
        total_pages = max(1, math.ceil(total_records / RECORDS_PER_PAGE))
        logger.debug(f"Total pages calculated: {total_pages}")
        
        # Ensure page is within valid range
        page = min(page, total_pages)
        logger.debug(f"Final page number: {page}")
        
        # Calculate start and end indices
        start_idx = (page - 1) * RECORDS_PER_PAGE
        end_idx = min(start_idx + RECORDS_PER_PAGE, total_records)
        logger.debug(f"Data range: {start_idx} to {end_idx}")
        
        # Get records for current page
        current_page_data = df.iloc[start_idx:end_idx].to_dict('records')
        logger.debug(f"Records for current page: {len(current_page_data)}")
        
        return render_template('list.html', 
                             data=current_page_data,
                             current_page=page,
                             total_pages=total_pages)
    except Exception as e:
        logger.error(f"Error in list_page: {str(e)}", exc_info=True)
        return render_template('list.html', 
                             data=[],
                             current_page=1,
                             total_pages=1)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            logger.debug(f"Processing file: {file.filename}")
            df = pd.read_csv(file)
            
            # Add Time column if it doesn't exist
            if 'Time' not in df.columns:
                df['Time'] = ''
                logger.debug("Added Time column")
            
            # Save the CSV
            csv_path = os.path.join(os.path.dirname(__file__), 'check_list.csv')
            df.to_csv(csv_path, index=False)
            logger.debug("CSV saved successfully")
            
            return render_template('list.html', 
                                 data=df.iloc[0:RECORDS_PER_PAGE].to_dict('records'),
                                 current_page=1,
                                 total_pages=max(1, math.ceil(len(df) / RECORDS_PER_PAGE)))
        
        logger.error("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/edit/<filename>')
def edit_image(filename):
    try:
        logger.debug(f"Editing image: {filename}")
        image_list = get_image_list()
        current_index = image_list.index(filename)
        
        prev_image = image_list[current_index - 1] if current_index > 0 else None
        next_image = image_list[current_index + 1] if current_index < len(image_list) - 1 else None
        
        return render_template('edit.html', 
                             filename=filename,
                             prev_image=prev_image,
                             next_image=next_image)
    except Exception as e:
        logger.error(f"Error in edit_image: {str(e)}", exc_info=True)
        return render_template('index.html')

@app.route('/image/<filename>')
def get_image(filename):
    try:
        logger.debug(f"Getting image: {filename}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error in get_image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 404

@app.route('/raw_image/<filename>')
def raw_image(filename):
    try:
        # Remove '_binary' from the filename
        raw_filename = filename.replace('_binary', '')
        logger.debug(f"Getting raw image: {raw_filename}")
        return send_from_directory(app.config['RAW_IMG_FOLDER'], raw_filename)
    except Exception as e:
        logger.error(f"Error in raw_image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 404

@app.route('/save', methods=['POST'])
def save_image():
    try:
        data = request.json
        filename = data['filename']
        logger.debug(f"Saving image: {filename}")
        
        image_data = data['image'].split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Save to output folder
        output_filename = f"{os.path.splitext(filename)[0]}_bgrm.jpg"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        image.save(output_path)
        logger.debug(f"Image saved to: {output_path}")
        
        # Update CSV status
        update_csv_status(filename)
        
        return jsonify({'success': True, 'message': 'Image saved successfully'})
    except Exception as e:
        logger.error(f"Error in save_image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True) 