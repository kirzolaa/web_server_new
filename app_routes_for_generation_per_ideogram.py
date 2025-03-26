#https://developer.ideogram.ai/api-reference/api-reference/generate
#https://developer.ideogram.ai/api-reference/api-reference/edit
#https://developer.ideogram.ai/api-reference/api-reference/remix
#https://developer.ideogram.ai/api-reference/api-reference/upscale
#https://developer.ideogram.ai/api-reference/api-reference/describe
#https://developer.ideogram.ai/api-reference/api-reference/reframe
#these are the offically implemented api functions in the ideogram api

def app_routes_for_generation_per_ideogram():
    @app.route('/api/generate', methods=['POST'])
    def generate():
        return jsonify({
            'success': True,
            'message': 'Generate endpoint not implemented'
        })