#ifndef SOFTAP
#define SOFTAP

#include "esp_netif.h"

void softap_init(void);

extern esp_netif_t *ap_netif;

#endif //SOFTAP