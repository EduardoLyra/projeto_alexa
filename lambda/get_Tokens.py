class Token():
    def time_zone(self, handler_input):
        self.sys_object = handler_input.request_envelope.context.system
        self.device_id = self.sys_object.device.device_id

        self.api_endpoint = self.sys_object.api_endpoint
        self.api_access_token = self.sys_object.api_access_token

        self.url = '{self.api_endpoint}/v2/devices/{self.device_id}/settings/System.timeZone'.format(
            api_endpoint=self.api_endpoint, device_id=self.device_id)
        self.headers = {'Authorization': 'Bearer ' + self.api_access_token}
        return self.url, self.headers

    def reminder(self, handler_input):
        self.sys_object = handler_input.request_envelope.context.system
        self.device_id = self.sys_object.device.device_id

        self.api_endpoint = self.sys_object.api_endpoint
        self.api_access_token = self.sys_object.api_access_token

        self.url = '{self.api_endpoint}/v1/alerts/reminders'.format(
            api_endpoint=self.api_endpoint)
        self.headers = {'Authorization': 'Bearer ' + self.api_access_token}
        return self.url, self.headers
