/*
  ===========================================
       Copyright (c) 2017 Stefan Kremser
              github.com/spacehuhn
        Modified 2023 Radutoiu Razvan
  ===========================================
*/


/* include all necessary libraries */ 
#include "freertos/FreeRTOS.h"
#include "esp_wifi.h"
#include "esp_private/wifi.h"
#include "lwip/err.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_event_loop.h"
#include "nvs_flash.h"
#include "driver/gpio.h"


//===== SETTINGS =====//
#define CHANNEL 1
#define BAUD_RATE 115200
#define CHANNEL_HOPPING true
#define MAX_CHANNEL 13
#define HOP_INTERVAL 214 //in ms

//===== Run-Time variables =====//
int ch = CHANNEL;
unsigned long lastChannelChange = 0;


//===== FUNCTIONS =====//

/* write packet to Serial */
void newPacketSerial(uint32_t len, uint8_t* buf){
  uint8_t _buf[4];
  _buf[0] = len;
  _buf[1] = len >>  8;
  _buf[2] = len >> 16;
  _buf[3] = len >> 24;
  Serial.write(_buf, 4);
  Serial.write(_buf, 4);
  
  Serial.write(buf, len);
}

/* will be executed on every packet the ESP32 gets while beeing in promiscuous mode */
void sniffer(void *buf, wifi_promiscuous_pkt_type_t type){

  wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
  wifi_pkt_rx_ctrl_t ctrl = (wifi_pkt_rx_ctrl_t)pkt->rx_ctrl;
  
  if (ctrl.sig_len > 2324) return; // pachet prea lung  if (ctrl.sig_len > SNAP_LEN) return; // 2324 // 293 // 2324 ia toate pachetele posibile
  uint32_t packetLength = ctrl.sig_len;
  if (type == WIFI_PKT_MGMT) packetLength -= 4; 
  // ultimii 4 biti sunt eronati

  if (type == WIFI_PKT_MGMT &&  pkt->payload[0] == 0x80) {
    
  } // beacon

  if (type == WIFI_PKT_MGMT &&  (pkt->payload[0] == 0xA0 || pkt->payload[0] == 0xC0 )) {
  //    deauths
  }

  if (( (pkt->payload[30] == 0x88 && pkt->payload[31] == 0x8e)|| ( pkt->payload[32] == 0x88 && pkt->payload[33] == 0x8e) )){
  //    eapols
  }

  newPacketSerial(packetLength, pkt->payload);
}

esp_err_t event_handler(void *ctx, system_event_t *event){ return ESP_OK; }


//===== SETUP =====//
void setup() {

  /* start Serial */
  Serial.begin(BAUD_RATE);
  Serial.println();

  /* setup wifi */
  nvs_flash_init();
  tcpip_adapter_init();
  ESP_ERROR_CHECK( esp_event_loop_init(event_handler, NULL) );
  wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
  ESP_ERROR_CHECK( esp_wifi_init(&cfg) );
  ESP_ERROR_CHECK( esp_wifi_set_storage(WIFI_STORAGE_RAM) );
  ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_NULL) );  
  ESP_ERROR_CHECK( esp_wifi_start() );

  Serial.println("<<START>>");
  
  ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
  ESP_ERROR_CHECK(esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE));
  ESP_ERROR_CHECK(esp_wifi_set_promiscuous_rx_cb(sniffer));
}

//===== LOOP =====//
void loop() {
  
  /* Channel Hopping */
  if(CHANNEL_HOPPING){
    unsigned long currentTime = millis();
    if(currentTime - lastChannelChange >= HOP_INTERVAL){
      lastChannelChange = currentTime;
      ch++;
      if(ch > MAX_CHANNEL) ch = 1;
      esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
    }
  }
  
}