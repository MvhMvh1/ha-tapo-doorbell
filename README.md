# Tapo Doorbell (lokaal) – Home Assistant

Leest de drukknop van een Tapo D130 lokaal uit. Geen cloud, geen Tapo-account, geen wachtwoord.

Bij elke druk op de knop stuurt de D130 een UDP-broadcast naar poort 20005 in je netwerk. Deze integratie luistert daarop en filtert op het IP-adres van de deurbel.

## Wat je krijgt

| Entiteit | Wat |
|---|---|
| `event.<naam>_deurbel` | Event-entiteit (device class `doorbell`), event type `ring`, bij elke druk |
| `binary_sensor.<naam>_ingedrukt` | Staat een paar seconden op `aan` na een druk (handig voor dashboards) |
| Bus-event `tapo_doorbell_ring` | Met `host`, `name`, `entry_id` |

## Installeren

1. Kopieer de map `custom_components/tapo_doorbell` naar `/config/custom_components/` (via Samba, File editor of Studio Code Server).
2. Herstart Home Assistant.
3. Instellingen → Apparaten & diensten → Integratie toevoegen → **Tapo Doorbell (lokaal)**.
4. Vul het IP-adres van de deurbel in. Geef de D130 een vast IP in UniFi, anders werkt het filter na een DHCP-wissel niet meer.

## Voorwaarden

- Home Assistant en de deurbel in hetzelfde VLAN/broadcastdomein (broadcasts gaan niet over routers heen).
- Bij een VM: netwerkadapter in bridged-modus, niet NAT. Inkomend UDP 20005 niet blokkeren.
- Werkt naast *Tapo: Cameras Control*; beide kunnen tegelijk op poort 20005 luisteren.

## Automatisering (voorbeeld)

```yaml
alias: Deurbel – melding
triggers:
  - trigger: state
    entity_id: event.tapo_d130_deurbel
    not_from: unavailable
actions:
  - action: notify.mobile_app_jouw_telefoon
    data:
      title: Deurbel
      message: Er staat iemand voor de deur
mode: single
```

## Opties

- **Herhaalde pakketten negeren** (standaard 5 s): één druk stuurt soms meerdere pakketten.
- **Sensor aan houden** (standaard 5 s).

## Problemen zoeken

Zet debuglogging aan in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.tapo_doorbell: debug
```

Druk op de bel en zoek in het logboek naar `Packet from <ip>`. Zie je niets, dan komt de broadcast niet bij de VM aan (netwerk/VLAN/firewall). Zie je een ander IP dan verwacht, pas dan het IP in de integratie aan.
