# compara_grib2
Compara arquivos gribados do NCEP (GFS) com tabelas de dados CSV

Uso: python compara_grib2_csv.py arquivo.grib2

## Bibliotecas necessárias

* numpy
* pandas
* pygrib

## Arquivos de limites (temperatura, geopotencial, umidade relativa e vento):

Formato (exemplo para temperatura em K):

```csv
Tabela Global de Temperatura (Mín,Máx) em Kelvin por Nível de Pressão e Latitude
Nível(hPa),-90° a -60°  (Antártica / Polar S),-60° a -30°  (Temp. Sul),-30° a 0°  (Subtrop./Trop. S),0° a 30°  (Trop./Subtrop. N),30° a 60°  (Temp. Norte),60° a 90°  (Ártico / Polar N)
(hPa),min1,max1,min2,max2,min3,max3,min4,max4,min5,max5,min6,max6
1000 ,225,265,268,295,288,308,290,318,258,305,238,285
900  ,223,260,265,290,283,303,285,308,255,298,235,280
850  ,220,258,262,285,280,298,281,303,252,295,232,275
800  ,218,253,260,280,276,295,277,298,248,291,228,270
700  ,212,245,253,273,270,288,271,290,242,283,222,263
600  ,205,238,245,265,262,278,263,280,235,275,215,255
500  ,198,230,235,255,252,268,253,270,225,265,208,248
300  ,185,215,215,235,230,243,231,245,212,238,200,225
200  ,180,215,208,225,212,220,212,222,208,225,195,225
100  ,185,220,210,225,190,198,191,199,212,225,195,228
50   ,180,225,212,228,195,205,196,206,210,230,190,235
```
 1. coluna  1: altura em pressão
 2. coluna  2: mínimo para latitudes de -90 a -60
 3. coluna  3: máximo para latitudes de -90 a -60
 4. coluna  4: mínimo para latitudes de -60 a -30
 5. coluna  5: máximo para latitudes de -60 a -30
 6. coluna  6: mínimo para latitudes de -30 a 0
 7. coluna  7: máximo para latitudes de -30 a 0
 8. coluna  8: mínimo para latitudes de   0 a 30
 9. coluna  9: máximo para latitudes de   0 a 30
10. coluna 10: mínimo para latitudes de  30 a 60
11. coluna 11: máximo para latitudes de  30 a 60
12. coluna 12: mínimo para latitudes de  60 a 90
13. coluna 13: máximo para latitudes de  60 a 90

Os valores nas tabelas são testes. Coloque os valores adequados.