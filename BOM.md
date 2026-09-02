# GestureDrive hardware BOM (no kits)

Street prices are USD estimates. Search the **query** column on Amazon or a hobby shop.

## Already on hand

| ID | Item | Qty | Action |
|---|---|---|---|
| HAVE-01 | ESP32 DevKit (Elegoo) | 1 | Keep — MCU + 2.4 GHz WiFi |
| HAVE-02 | Laptop + webcam | 1 | Keep — MediaPipe host |
| HAVE-03 | Lab 3D printer, solder, PSU, scope | — | Confirm PETG or PLA+ and a soldering iron |

## Buy now (~$86–$107, midpoint ~$95)

| ID | Item | Qty | Est. | Search query | Why |
|---|---|---|---|---|---|
| GD-01 | TT geared DC motors 3–6 V | 2 | $6–$10 | `TT motor dual shaft robot 2 pack` | Rear drive |
| GD-02 | 65 mm rubber wheels, TT hub | 4 | $6–$10 | `65mm robot wheel TT motor` | 2 driven, 2 steered |
| GD-03 | 608 bearings 8x22x7 mm | 10-pack | $4–$6 | `608 skate bearing 10 pack` | Front hubs / knuckles |
| GD-04 | L298N dual H-bridge | 2 | $8–$10 | `L298N motor driver module` | 1 on car + 1 spare |
| GD-05 | MG996R metal-gear servo | 1 | $7–$12 | `MG996R servo metal gear` | Steering; skip SG90 |
| GD-06 | 5 V 3 A buck LM2596 or MP1584 | 1 | $4–$6 | `LM2596 buck converter 3A` | ESP32 + servo rail |
| GD-07 | 2S LiPo 7.4 V 1000–1500 mAh + balance charger | 1 combo | $20–$28 | `2S 7.4V 1500mAh LiPo charger T plug` | You have no pack |
| GD-08 | LiPo fire bag | 1 | $8 | `LiPo battery fire bag` | Charge/store only in this |
| GD-09 | SPST toggle + 3 A polyfuse | 1 each | $4 | `12V toggle switch 3A polyfuse` | Kill switch on pack + |
| GD-10 | XT60 or T-plug pigtails + 18–22 AWG | 1 pack | $6 | `XT60 pigtail 16AWG` | Pack to L298N VMS |
| GD-11 | M3 screws/nuts/standoffs + M3 heat-set inserts | 1 | $8–$12 | `M3 heat set inserts knurled 3D print` | Printed mounts |
| GD-12 | Mini breadboard + Dupont jumpers | 1 | $6–$8 | `mini breadboard jumper wire pack` | Signal wiring |
| GD-13 | Swivel caster | 1 | $3 | `robot swivel caster 1 inch` | 2WD fallback if steering binds |

## Power rules

- 2S 7.4 V into L298N **VMS** (motor supply). Remove the L298N 5 V jumper if VMS > 12 V; at 7.4 V the onboard 5 V regulator can feed logic **or** use the buck for logic and leave the jumper off if the regulator runs hot.
- Buck the same pack to 5 V for ESP32 5 V pin and servo V+.
- Common ground: pack −, L298N GND, ESP32 GND, servo GND, buck GND.
- Never power the servo from the ESP32 5 V pin.
- No 3S 11.1 V into L298N. No 1S 3.7 V pack.

## Print after parts arrive

See `hardware/openscad/`. Print P1 coupons first, then P2 2WD base, then P3 Ackermann, then P4 cages.
