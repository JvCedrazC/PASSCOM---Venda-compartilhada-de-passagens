import json
import socket
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import requests  # Usaremos a biblioteca requests para fazer requisições HTTP
from collections import deque