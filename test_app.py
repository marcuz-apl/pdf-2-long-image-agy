import unittest
import io
import json
import os
import shutil
from app import app, TEMP_DIR

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        # Clean up TEMP_DIR after tests
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PDF<span class="accent">2</span>LongImage', response.data)

    def test_upload_no_files(self):
        response = self.app.post('/upload')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'No files uploaded')

    def test_download_invalid_job_id(self):
        # job_id is not a valid UUID
        response = self.app.get('/download/invalid-job-id/file.tiff')
        self.assertEqual(response.status_code, 400)

    def test_download_path_traversal(self):
        # job_id is valid uuid structure, but filename is malicious traversal
        malicious_job_id = '123e4567-e89b-12d3-a456-426614174000'
        
        # Testing with non-alphanumeric chars or traversal
        # Flask routing or our validation should reject these with 400 or 404
        response = self.app.get(f'/download/{malicious_job_id}/../../etc/passwd')
        self.assertIn(response.status_code, [400, 404])

        response = self.app.get(f'/download/{malicious_job_id}/C:\\windows\\win.ini')
        self.assertIn(response.status_code, [400, 404])

if __name__ == '__main__':
    unittest.main()
