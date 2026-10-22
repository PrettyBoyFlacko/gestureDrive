idf_component_register(SRCS "main.c" "softap.c" "udp_client.c"
                    PRIV_REQUIRES esp_wifi nvs_flash
                    INCLUDE_DIRS ".")
