# -*- coding: utf-8 -*-

__author__    = 'Kazuyuki TAKASE'
__copyright__ = 'PLEN Project Company Inc, and all authors.'
__license__   = 'The MIT License (http://opensource.org/licenses/mit-license.php)'


# 外部プログラムの読み込み
# =============================================================================
from bottle import Bottle, request, response, static_file
from cv2 import VideoCapture, imencode
from paste import httpserver
from wiringpi import *

from adc import analogRead


# 定数定義・初期化処理
# =============================================================================
LIGHT_PIN    = 0
THERMO_PIN   = 1
VOLUME_PIN   = 2
MOTION_PIN   = 26
SERVO_PIN    = 18
CAMERA_INDEX = 0

camera = VideoCapture(CAMERA_INDEX)
router = Bottle()

wiringPiSetupGpio()
pinMode(SERVO_PIN, PWM_OUTPUT)
pwmSetMode(PWM_MODE_MS)
pwmSetRange(1024)
pwmSetClock(375)


# URIの定義・HTTPサーバの起動
# =============================================================================
def enable_cors(fn):
    '''
    @brief Enable CORS (Cross Origin Resource Sharing) decorator.

    @param [in, out] fn Routing method

    @return Decorated *fn*
    '''

    def _enable_cors(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin' ] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if request.method != 'OPTIONS':
            # Actual request; reply with the actual response.
            return fn(*args, **kwargs)

    return _enable_cors


@router.route('/v3/image', method=['OPTIONS', 'GET'])
@enable_cors
def image_get():
    [ camera.read() for _ in xrange(5) ]
    
    _, frame = camera.read()
    _, image = imencode('.jpg', frame)

    response.headers['Cache-Control'] = 'no-cache'
    response.content_type = 'image/jpg'

    return image.tobytes()


@router.route('/v3/sensor', method=['OPTIONS', 'GET'])
@enable_cors
def sensor_get():
    response_json = {
        'resource': 'sensor',
        'data': {
            'light': analogRead(LIGHT_PIN),
            'thermo': analogRead(THERMO_PIN),
            'volume': analogRead(VOLUME_PIN),
            'motion': digitalRead(MOTION_PIN)
        }
    }

    response.headers['Cache-Control'] = 'no-cache'
    response.content_type = 'application/json'

    return response_json


@router.route('/v3/servo', method=['OPTIONS', 'PUT'])
@enable_cors
def servo_put():
    pwm = request.json['pwm']

    response_json = {
        'resource': 'servo',
        'data': {
            'command': 'pwm_write',
            'result': pwmWrite(SERVO_PIN, max(min(pwm, 123), 26))
        }
    }

    response.headers['Cache-Control'] = 'no-cache'
    response.content_type = 'application/json'

    return response_json


httpserver.serve(router, host='0.0.0.0', port=80)
