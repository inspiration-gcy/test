import json
from base64 import b64encode
from http.client import HTTPConnection
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


class NxtCameraStream:
    mock_ips = ["NXT-MOCK.254.44.35", "NXT-MOCK.254.48.55", "NXT-MOCK.254.25.16"]

    def __init__(self, cam_ip):
        self.ip_address = cam_ip
        self.is_mock = cam_ip in self.mock_ips

        # adding the authentification to the REST header. The standard password is "ids".
        # The admin user is required to configure the Vision Apps
        self.header = self.set_authentification('admin', 'ids')
        self.nxt = HTTPConnection(self.ip_address)

        if not self.is_mock:

            self.image_header = self.header.copy()
            self.image_header['Accept'] = 'image/jpeg'
            self.image = None

            # get and set frame size
            self.nxt.request('GET', '/camera/roi', headers=self.header)
            result_image = self.nxt.getresponse().read()
            json_result_image = json.loads(result_image.decode())

            self.frame_width = json_result_image['Width']
            self.frame_height = json_result_image['Height']

            # requesting a first image
            self.nxt.request('GET', '/camera/image', headers=self.image_header)
            response = self.nxt.getresponse()
            if response.status != 200:
                print('Error Code:', response.status)

            # and reading out the image's etag and saving it for reference
            self.etag = response.getheader("etag")
            if self.etag:
                self.image_bytes = response.read()
                self.image = Image.open(BytesIO(self.image_bytes))

        # The image is provided in RGB format but has to transformed into BGR for the opencv display
        # image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        # cv2.imshow("video", np.array(image))

        else:
            self.frame_width = 800
            self.frame_height = 600

        # set and encode authentification

    @staticmethod
    def set_authentification(username, password):
        header = {}
        b64_authorisation = b64encode(bytes(username + ':' + password, "utf-8")).decode("ascii")
        header['Authorization'] = 'Basic %s' % b64_authorisation
        header['Content-Type'] = 'application/x-www-form-urlencoded'
        return header

    # Setting up a live image read out using image etags. Each image is generated with a unique etag and only transmitted
    # if a new etag is available to save bandwidth.
    def get_frame(self):

        if not self.is_mock:
            # An "If-None-Match" condition for the etag is added to the header. This way images are only requested if the
            # etags don't match. This ensures that only new images are transmitted
            # image_header['If-None-Match'] = etag
            self.nxt.request('GET', '/camera/image', headers=self.image_header)
            response = self.nxt.getresponse()

            # If the etags match and no new image is available yet, the response status will be 304. This status is
            # to be expected and not treated as an error
            if response.status not in [200, 304]:
                print('Error Code:', response.status)
            else:
                # In case a new image has been provided, the etag is updated and the image read out and displayed in the
                # generated opencv window "video"
                self.etag = response.getheader("etag")
                if self.etag:
                    self.image_bytes = response.read()
                    self.image = Image.open(BytesIO(self.image_bytes))
                    self.image = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2BGR)
                # cv2.imshow("video", np.array(image))

                if len(self.image) > 0:
                    hasFrame = True
                else:
                    hasFrame = False

                return hasFrame, self.image

        else:
            return True, cv2.imread("app/base/static/assets/images/nxt_mock.png")

    def get_label(self):

        if not self.is_mock:
            # This ressource gives access to the latest result in memory.
            # The .../list ressource stores several results named by the etag of the corresponding image.
            # Such the result can be unambiguously assigned to their image
            nxt = HTTPConnection(self.ip_address)
            nxt.request('GET', '/vapps/cnnmanager/resultsources/last', headers=self.header)
            response = nxt.getresponse()

            data = json.loads(response.read().decode())

            result = {'Class': data['inference']['Top1'],
                      'Confidence': data['inference_propability']['Top1']}

            if response.status != 200:
                print('Error Code:', response.status)

            if float(result['Confidence']) > 0.3:
                return result['Class']
            else:
                return None

        else:
            return "NXT Mock"

    # Gets a list of installed CNN models from the NXT CNN Manager
    # @Krste MAKE SURE THE CNN Manager VAPP IS SWITCHED ON on camera boot
    def get_installed_cnns(self):

        if not self.is_mock:

            self.nxt.request('OPTIONS', '/vapps/cnnmanager/configurables', headers=self.header)
            response = self.nxt.getresponse()

            if response.status != 200:
                print('Error Code:', response.status)

            response = response.read()
            cnn_list = json.loads(response.decode())['GET']['application/json']['Values']['packages']['Range']
            print('LVL1_NXT_modelList found', cnn_list, 'model(s) at IP address', self.ip_address)
            return cnn_list

    # switching between insalled CNN models in the CNN Manager using the PATCH request to modify an existing ressource
    def switch_cnn_model(self, new_model):

        if not self.is_mock:
            print("Switching CNN" + new_model)

            self.nxt.request('PATCH', '/vapps/cnnmanager/configurables', 'packages=' + new_model, headers=self.header)
            response = self.nxt.getresponse()

            if response.status != 200:
                print('Error Code:', response.status)

            response.read()
            return new_model

    # Gets a list of installed CNN models from the CNN Manager.
    # Since the models can be switched via the REST interface, this ressource can be accessed via the Vapp's configurables
    # PLEASE MAKE SURE THE CNN Manager VAPP IS SWITCHED ON ON YOUR DEVICE!
    def upload_cnn_model(self, model_directory):

        if not self.is_mock:
            print("Uploading CNN" + model_directory)

            # The REST header is modified for file upload
            upload_header = self.header.copy()
            upload_header['Content-Type'] = 'application/octet-stream'
            with open(model_directory, 'rb') as file:
                # For adding ressources, the PUT request is used
                self.nxt.request('PUT', '/vapps/cnnmanager/files/cnnfile/data', file.read(), headers=upload_header)
                response = self.nxt.getresponse()

                if response.status != 200:
                    print('Error Code:', response.status)

                response.read()
