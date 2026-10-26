"""Constants for the Tapo Doorbell integration."""

DOMAIN = "tapo_doorbell"

CONF_COOLDOWN = "cooldown"
CONF_PULSE = "pulse"
CONF_STREAM = "stream"

DEFAULT_NAME = "Tapo D130"
DEFAULT_COOLDOWN = 5  # seconds: one press often sends several packets
DEFAULT_PULSE = 5  # seconds the binary sensor stays "on"
DEFAULT_STREAM = "stream1"  # stream1 = high quality, stream2 = low quality
STREAMS = ["stream1", "stream2"]

UDP_PORT = 20005
RTSP_PORT = 554
DISCOVERY_TIMEOUT = 60  # seconds to wait for a press during setup

EVENT_RING = "tapo_doorbell_ring"  # fired on the HA event bus at the press
EVENT_SNAPSHOT = "tapo_doorbell_snapshot"  # fired once the photo is ready
SIGNAL_PACKET = f"{DOMAIN}_packet_{{}}"  # formatted with the doorbell IP
SIGNAL_RING = f"{DOMAIN}_ring_{{}}"  # formatted with the config entry id

DATA_LISTENER = "listener"
