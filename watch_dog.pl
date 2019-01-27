#!/usr/bin/perl


#################################################
# Мониторинг работы server.py и его перезапуск  #
#################################################

$reload=0;

open(F, 'ps | grep server.py | wc -l |');
  while ($line=<F>)
    {
    if ($line < 1)
      {
      $reload=1;
      }
    }
close(F);

#$reload = 0;

if ($reload == 1)
    {
    system "/home/pi/tank/server.py >>/home/pi/tank/log.txt 2>&1";
    }

####################################################
# Мониторинг работы client_bot.py и его перезапуск #
####################################################


$reload=0;

open(F, 'ps | grep client_bot.py | wc -l |');
  while ($line=<F>)
    {
    if ($line < 1)
      {
      $reload=1;
      }
    }
close(F);

#$reload = 0;

if ($reload == 1)
    {
    system "/home/pi/tank/client_bot.py";
    }

