import flask
import json
from syrabond import common
from syrabond.api import API


conf = common.extract_config('global.json')
api = API(conf['facility_name'])
conf.clear()
app = flask.Flask(__name__)


@app.route('/api/v02/<path:params>', methods=['GET', 'POST'])
def get_api_request(params):
    #print(params)
    return json.dumps(api.parse_request(params), ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/api/v02/<path:params>', methods=['GET', 'POST'])
def postapi_request(params):
    #print(params)
    return json.dumps(api.parse_request(params), ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/client', methods=['GET'])
def index():
    return flask.redirect("/client/index", code=302)


@app.route('/client/<page>', methods=['GET'])
def client(page):
    print(page)
    return open('./clientside/{}.html'.format(page)).read()


@app.route('/client/test/<tst>', methods=['GET'])   # test jsons
def test(tst):
    return open('./clientside/{}'.format(tst)).read()


@app.route('/client/include/<path:params>', methods=['GET'])   # test jsons
def include(params):
    print(params)
    if params.find('css') > -1:
        return flask.send_file('./clientside/include/'+params, mimetype='text/css')
    else:
        return flask.send_file('./clientside/include/'+params, mimetype='text/html')


@app.route('/client/img/<filename>', methods=['GET'])
def give_image(filename):
    return flask.send_file('./clientside/'+filename, mimetype='image/gif')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
