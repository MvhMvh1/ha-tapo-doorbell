"""Constants for the Tapo Doorbell integration."""

DOMAIN = "tapo_doorbell"

CONF_COOLDOWN = "cooldown"
CONF_PULSE = "pulse"

DEFAULT_NAME = "Tapo D130"
DEFAULT_COOLDOWN = 5  # seconds: one press often sends several packets
DEFAULT_PULSE = 5  # seconds the binary sensor stays "on"

UDP_PORT = 20005

EVENT_RING = "tapo_doorbell_ring"  # fired on the HA event bus
SIGNAL_PACKET = f"{DOMAIN}_packet_{{}}"  # formatted with the doorbell IP
SIGNAL_RING = f"{DOMAIN}_ring_{{}}"  # formatted with the config entry id

DATA_LISTENER = "listener"
