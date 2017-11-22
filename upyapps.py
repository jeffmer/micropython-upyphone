# UpyPhone Apps 
# MIT License; Copyright (c) 2017 Jeffrey N. Magee


import ui

class AppScreen(ui.Screen):

    def __init__(self, lcd, backfn, label, fg=ui.WHITE, bg=ui.BLACK, bb=ui.BLUE):
        super().__init__(lcd, fg, bg)
        self.bb = bb
        self.name =  ui.Label(self,0,0,128,20,self.fg,self.bg,label)
        self.back  = ui.Button(self,88,135,30,20,self.fg,self.bb,'Bk')
        self.back.callback(backfn)
        
class ManageAppScreen(AppScreen):
        
    def __init__(self, lcd, backfn, label = 'UpyApps'):  
        super().__init__(lcd,backfn,label)   
        self.apps =[]
        
    def install(self,  newapp, fn):
        self.apps.append(ui.Button(self,10,len(self.apps)*30+30,108,20,ui.FG,ui.GREEN, newapp.name.label))
        self.apps[-1].callback(fn)
    
        
class CurrencyApp(AppScreen):

    def __init__(self, lcd, phone, backfn, label = 'Currency'):  
        self.phone = phone
        super().__init__(lcd,backfn,label)
        self.euro = ui.Label(self,10,40,108,10,ui.FG,  ui.GREY,"Euro       :",1,0,False)
        self.dollar = ui.Label(self,10,55,108,10,ui.FG,ui.GREY,"US Dollar  :",1,0,False)
        self.swiss = ui.Label(self,10,70,108,10, ui.FG,ui.GREY,"Swiss Franc:",1,0,False)
        self.status = ui.Label(self,0,125,60,10, self.fg,self.bg,"",1,0)
        self.update  = ui.Button(self,0,135,60,20,ui.FG,ui.BLUE,'Update')
        self.update.callback(self.do_update)
        
    def do_update(self):
        self.status.set_text('Fetching..')
        r = self.phone.http_get("https://v3.exchangerate-api.com/bulk/** your API KEY ***/GBP")
        if r and r.status==200:
            eur = '{:4.3f}'.format(r.json()['rates']['EUR'])
            usd = '{:4.3f}'.format(r.json()['rates']['USD'])
            chf = '{:4.3f}'.format(r.json()['rates']['CHF'])
            self.euro.set_text  ('Euro       : {}'.format(eur))
            self.dollar.set_text('US Dollar  : {}'.format(usd ))
            self.swiss.set_text('Swiss Franc: {}'.format(chf))
        self.status.set_text('')
        r.close()
                               
        
icontofile = {
    "clear":"clear",
    "cloudy":"cloudy",
    "flurries":"snow",
    "fog":"fog",
    "hazy":"fog",
    "mostlycloudy":"partlycloudy",
    "partlycloudy":"partlycloudy",
    "mostlysunny":"partlycloudy",
    "sleet":"sleet",
    "rain":"rain",
    "snow":"snow",
    "tstorms":"tstorms"
}
        
class WeatherApp(AppScreen):

    def __init__(self, lcd, phone, backfn, label = 'Weather'):  
        self.phone = phone
        super().__init__(lcd,backfn,label,ui.WHITE,ui.BLACK,ui.GREY)
        y = const(30)
        self.city = ui.Label(self,10,y-10,108,10,self.fg,self.bg,"City",1,1)
        self.weather = ui.Label(self,10,y,108,10,self.fg,self.bg,"Weather",1,0)
        self.icon = ui.Image(self,72,y+15,50,50,None)
        self.temperature = ui.Label(self,10,y+15,54,20,self.fg,self.bg,"Temp",3,1,False)
        self.humidity = ui.Label(self,10,y+35,54,10,self.fg,self.bg,"Humidity",1,0,False)
        self.pressure = ui.Label(self,10,y+45,54,10,self.fg,self.bg,"Pressure",1,0,False)
        self.wind = ui.Label(self,10,y+55,54,10,self.fg,self.bg,"Wind",1,0,False)
        self.sunrise = ui.Label(self,10,y+75,80,10,self.fg,self.bg,"Sunrise",1,0,False)
        self.sunset = ui.Label(self,10,y+85,80,10,self.fg,self.bg,"Sunset",1,0,False)
        self.location1  = ui.Button(self,0,135,30,20,self.fg,self.bb,'Lon')
        self.location1.callback(lambda x = 'GB/London': self.do_update(x))
        self.location2  = ui.Button(self,40,135,30,20,self.fg,self.bb,'Ros')
        self.location2.callback(lambda x = 'FR/Roscoff': self.do_update(x))


 
    def do_update(self,place):
        self.weather.set_text('fetching..')
        r = self.phone.http_get('http://api.wunderground.com/api/** your API KEY ***/conditions/astronomy/q/{}.json'.format(place))
        dd=r.json()
        if r and r.status == 200:
            self.weather.set_text('{}'.format(dd['current_observation']['weather']))
            self.city.set_text('{}, {}'.format(dd['current_observation']['display_location']['city'],
                                               dd['current_observation']['display_location']['country'],))
            self.temperature.set_text('{}C'.format(dd['current_observation']['temp_c']))
            self.humidity.set_text('{}'.format(dd['current_observation']['relative_humidity']))
            self.pressure.set_text('{}mb'.format(dd['current_observation']['pressure_mb']))
            self.wind.set_text('{}mph {}'.format(int(dd['current_observation']['wind_mph']),
                                       dd['current_observation']['wind_dir']))
            self.sunrise.set_text('Sunrise {}:{}'.format(dd['moon_phase']['sunrise']['hour'],
                                                         dd['moon_phase']['sunrise']['minute']))
            self.sunset.set_text('Sunset {}:{}'.format(dd['moon_phase']['sunset']['hour'],
                                                       dd['moon_phase']['sunset']['minute']))
            iconname =  dd['current_observation']['icon']
            with open('icons/{}.jpg'.format(icontofile[iconname]), 'rb') as f:
                buf = f.read()       
            self.icon.set_image(buf)
            r.close()
        else:
            if not r:
                self.weather.set_text('ERROR')
            else:
                self.weather.set_text('ERROR {}'.format(r.status))                       
        
        
