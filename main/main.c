#include "udp_client.h"
#include "softap.h"

void app_main(void)
{  
    softap_init();          // Init Wifi Access Point
    udp_client_init();      // Init UDP client
}
