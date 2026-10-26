# Tapo Doorbell (lokaal) – Home Assistant

Leest de drukknop van een Tapo D130 lokaal uit en maakt (optioneel) een foto bij elke druk. Geen cloud, geen TP-Link-account.

Bij elke druk op de knop stuurt de D130 een UDP-broadcast naar poort 20005 in je netwerk. Deze integratie luistert daarop en filtert op het IP-adres van de deurbel. De foto komt via RTSP van de camera zelf.

## Wat je krijgt

| Entiteit | Wat |
|---|---|
| `event.<naam>_deurbel` | Event-entiteit (device class `doorbell`), event type `ring`, direct bij elke druk |
| `binary_sensor.<naam>_ingedrukt` | Staat een paar seconden op `aan` na een druk (handig voor dashboards) |
| `image.<naam>_bezoeker` | Foto van het moment van aanbellen (alleen met camera-account) |
| Bus-event `tapo_doorbell_ring` | Direct bij de druk: `host`, `name`, `entry_id` |
| Bus-event `tapo_doorbell_snapshot` | Zodra de foto klaar is: `entity_id`, `url`, `entry_id` |

## Installeren

**Via HACS (aanbevolen)**
1. HACS → ⋮ → *Aangepaste repositories* → `https://github.com/MvhMvh1/ha-tapo-doorbell`, type *Integratie*.
2. Zoek *Tapo Doorbell (lokaal)*, installeer en herstart Home Assistant.

**Handmatig**: kopieer `custom_components/tapo_doorbell` naar `/config/custom_components/` en herstart.

## Instellen

Instellingen → Apparaten & diensten → Integratie toevoegen → **Tapo Doorbell (lokaal)**.

1. Kies **Zoeken: ik druk op de deurbel** en druk binnen 60 seconden op de knop. Het IP wordt automatisch gevonden. (Of vul het IP zelf in.)
2. Optioneel: vul het **camera-account** in voor foto's. Maak dat aan in de Tapo-app: deurbel → Instellingen → Geavanceerde instellingen → Camera-account. Dit is níet je TP-Link-login.

Camera-account later toevoegen of wijzigen kan via *Configureren* bij de integratie.

## Voorwaarden

- Home Assistant en de deurbel in hetzelfde VLAN/broadcastdomein (broadcasts gaan niet over routers heen).
- Bij een VM: netwerkadapter in bridged-modus, niet NAT.
- Geef de deurbel een vast IP-adres in je router.
- Voor foto's: RTSP (TCP 554) bereikbaar.
- Werkt naast *Tapo: Cameras Control*; beide kunnen tegelijk op poort 20005 luisteren.

## Automatiseringen

**Melding met foto** (trigger op de foto, zodat die er al is als de melding komt):

```yaml
alias: Deurbel – melding met foto
triggers:
  - trigger: state
    entity_id: image.tapo_d130_bezoeker
    not_from: unavailable
actions:
  - action: notify.mobile_app_jouw_telefoon
    data:
      title: Deurbel
      message: Er staat iemand voor de deur
      data:
        image: /api/image_proxy/image.tapo_d130_bezoeker
mode: single
```

**Direct iets doen bij de druk** (zonder op de foto te wachten), bijvoorbeeld lampen laten knipperen:

```yaml
triggers:
  - trigger: state
    entity_id: event.tapo_d130_deurbel
    not_from: unavailable
```

## Opties

- **Camera-account / kwaliteit**: hoog (stream1) is scherper, laag (stream2) sneller.
- **Herhaalde pakketten negeren** (standaard 5 s): één druk stuurt soms meerdere pakketten.
- **Sensor aan houden** (standaard 5 s).

## Problemen zoeken

```yaml
logger:
  logs:
    custom_components.tapo_doorbell: debug
```

Druk op de bel en zoek in het logboek naar `Packet from <ip>`. Zie je niets, dan komt de broadcast niet bij Home Assistant aan (netwerk/VLAN/firewall). Geen foto? Controleer het camera-account en of poort 554 bereikbaar is.
