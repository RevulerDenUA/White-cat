"""Author compact engineering catalogs and independently executable formula examples."""
import copy
import json
import math
from pathlib import Path
from science import *
from prepare_data import ROOT, CONFIG, read, write

PARAMETERS='https://ssd.jpl.nasa.gov/astro_par.html'
PLANETS='https://ssd.jpl.nasa.gov/planets/phys_par.html'
ROVER='https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/'
DERIVATION='docs/PHYSICS.md'

def quantity(value,unit,status,source,note=''):
    return dict(value=value,unit=unit,status=status,source=source,note=note)

def constants():
    values={
      'G':quantity(G,'m^3 kg^-1 s^-2','published',PARAMETERS,'CODATA 2018; finite uncertainty, not exact'),
      'c':quantity(C,'m s^-1','exact',PARAMETERS),
      'au':quantity(AU,'m','exact',PARAMETERS),
      'day':quantity(86400,'s','exact',PARAMETERS),
      'sigma':quantity(SIGMA,'W m^-2 K^-4','derived_from_exact_SI','https://physics.nist.gov/cgi-bin/cuu/Value?sigma'),
      'R_gas':quantity(8.31446261815324,'J mol^-1 K^-1','derived_from_exact_SI','https://physics.nist.gov/cgi-bin/cuu/Value?r'),
      'g0':quantity(9.80665,'m s^-2','conventional','https://physics.nist.gov/cgi-bin/cuu/Value?gn','Isp convention, not local Mars gravity'),
      'mu_sun':quantity(MU_SUN,'m^3 s^-2','published',PARAMETERS,'DE440 solar GM'),
      'earth_mass':quantity(EARTH_MASS,'kg','published_rounded',PLANETS),
      'earth_mean_radius':quantity(EARTH_RADIUS,'m','published',PLANETS),
      'sun_mass':quantity(MU_SUN/G,'kg','derived',PARAMETERS,'GM_sun / G; not an independent exact mass'),
      'sun_radius':quantity(695700000,'m','nominal','https://www.iau.org/static/resolutions/IAU2015_English.pdf'),
      'sun_luminosity':quantity(SOLAR_LUMINOSITY,'W','nominal','https://www.iau.org/static/resolutions/IAU2015_English.pdf'),
      'mars_mu':quantity(MARS_MU,'m^3 s^-2','published','https://ssd.jpl.nasa.gov/horizons/','Mars body GM from cached physical header; do not use Mars system GM'),
      'mars_mean_radius':quantity(MARS_RADIUS,'m','published','https://ssd.jpl.nasa.gov/horizons/','3389.92 km from cached header; uncertainty 0.04 km'),
      'mars_projection_radius':quantity(3396190,'m','cartographic_convention','https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic','Sphere used in supplied CTX rasters, separate from physical mean radius'),
      'mars_solar_day':quantity(MARS_SOL,'s','published','https://ssd.jpl.nasa.gov/horizons/'),
      'mars_sidereal_day':quantity(24.622962*3600,'s','published','https://ssd.jpl.nasa.gov/horizons/'),
      'mars_game_gravity':quantity(3.71,'m s^-2','rounded_model','https://ssd.jpl.nasa.gov/horizons/','Fixed surface mobility approximation, not computed at mean-radius level'),
    }
    write('data/physics/physical_constants.json',dict(schema_version='1.0',constants=values))

def formulas():
    # symbol: (SI unit, definition). Arguments match tools/science.py exactly.
    specs=[
    ('gravity','g=G*M/R^2','Прискорення на сферичній поверхні',{'M':('kg','маса тіла'),'R':('m','радіус')},{'M':EARTH_MASS,'R':EARTH_RADIUS},'m s^-2','Сферичне тіло; без обертання й гармонік поля.'),
    ('density','rho=3*M/(4*pi*R^3)','Середня об’ємна густина',{'M':('kg','маса'),'R':('m','об’ємний радіус')},{'M':EARTH_MASS,'R':EARTH_RADIUS},'kg m^-3','Не поверхнева густина; радіус газового гіганта залежить від рівня тиску.'),
    ('mass_from_density','M=4*pi*rho*R^3/3','Узгодження маси з радіусом і густиною',{'rho':('kg m^-3','середня густина'),'R':('m','радіус')},{'rho':5514,'R':EARTH_RADIUS},'kg','Густину не обирати незалежно від складу й стискання великих планет.'),
    ('period','P=2*pi*sqrt(a^3/mu)','Період еліптичної орбіти',{'a':('m','велика піввісь'),'mu':('m^3 s^-2','G*(M_star+M_planet)')},{'a':AU,'mu':MU_SUN},'s','Два тіла; a>0. Ігнорування маси планети допустиме при M_planet << M_star.'),
    ('vis_viva','v=sqrt(mu*(2/r-1/a))','Орбітальна швидкість у точці',{'mu':('m^3 s^-2','гравітаційний параметр'),'r':('m','миттєва відстань'),'a':('m','велика піввісь')},{'mu':MU_SUN,'r':AU,'a':AU},'m s^-1','Незбурена кеплерова орбіта; підкореневий вираз має бути невід’ємним.'),
    ('escape_speed','v_escape=sqrt(2*mu/R)','Швидкість втечі',{'mu':('m^3 s^-2','GM'),'R':('m','радіус')},{'mu':MARS_MU,'R':MARS_RADIUS},'m s^-1','Без атмосфери та обертання; не повний launch delta-v.'),
    ('rotation_speed','v_equator=2*pi*R/P','Екваторіальна швидкість обертання',{'R':('m','екваторіальний радіус'),'P':('s','модуль сидеричного періоду')},{'R':3396190,'P':24.622962*3600},'m s^-1','Жорстке обертання, окремо зберігати напрямок і нахил осі.'),
    ('rotation_breakup','P_break=2*pi*sqrt(R^3/(G*M))','Нижня оцінка періоду гравітаційного утримання',{'M':('kg','маса'),'R':('m','радіус')},{'M':EARTH_MASS,'R':EARTH_RADIUS},'s','Баланс GM/R^2=omega^2*R; без міцності. Генератор вимагає запас >=2.'),
    ('solar_day','P_solar=1/abs(1/P_rot-1/P_orb)','Сонячна доба проти сидеричної',{'P_rot':('s','знаковий сидеричний період; retrograde<0'),'P_orb':('s','орбітальний період')},{'P_rot':24.622962*3600,'P_orb':686.98*86400},'s','Кругова орбіта, нульовий нахил у наближенні середньої доби; при синхронізації повернути null/locked, не Infinity.'),
    ('irradiance','S=L/(4*pi*r^2)','Потік випромінювання на відстані',{'L':('W','болометрична світність'),'r':('m','відстань до зорі')},{'L':SOLAR_LUMINOSITY,'r':AU},'W m^-2','Ізотропне випромінювання; без поглинання між зорею і планетою.'),
    ('equilibrium_temperature','T_eq=(S*(1-A)/(4*sigma*epsilon))^(1/4)','Радіаційна рівноважна температура',{'S':('W m^-2','потік'),'A':('1','Bond альбедо'),'epsilon':('1','теплова випромінювальна здатність')},{'S':SOLAR_LUMINOSITY/(4*math.pi*AU**2),'A':.3,'epsilon':1},'K','Повне перерозподілення тепла, без парникового ефекту й внутрішнього тепла. Не температура поверхні й не geometric albedo.'),
    ('stellar_luminosity','L=4*pi*R^2*sigma*T^4','Світність за ефективною температурою',{'R':('m','радіус зорі'),'T':('K','ефективна температура')},{'R':695700000,'T':5772},'W','Болометричне наближення; не спектральна яскравість в окремому фільтрі.'),
    ('atmosphere_scale_height','H=R_gas*T/(m_mol*g)','Ізотермічна висота атмосфери',{'T':('K','температура газу'),'m_mol':('kg mol^-1','середня молярна маса'),'g':('m s^-2','прискорення')},{'T':210,'m_mol':.04334,'g':3.71},'m','Ідеальний газ, постійні T,g,склад; не профіль усієї атмосфери.'),
    ('barometric_pressure','p(z)=p0*exp(-z/H)','Тиск над опорним рівнем',{'p0':('Pa','опорний тиск'),'z':('m','висота над опорним рівнем'),'H':('m','масштаб висоти')},{'p0':610,'z':1000,'H':10800},'Pa','Ізотермічна гідростатика; p0 не глобальний тиск Єзеро.'),
    ('hohmann_time','t=pi*sqrt(((r1+r2)/2)^3/mu)','Час ідеального перельоту Земля–Марс',{'r1':('m','радіус внутрішньої орбіти'),'r2':('m','радіус зовнішньої орбіти'),'mu':('m^3 s^-2','GM центрального тіла')},{'r1':AU,'r2':1.523679*AU,'mu':MU_SUN},'s','Половина періоду еліпса; кругові компланарні орбіти, не розрахунок вікна запуску.'),
    ('departure_c3','C3=(sqrt(mu*(2/r1-2/(r1+r2)))-sqrt(mu/r1))^2','Характеристична енергія ідеального відльоту',{'r1':('m','початковий радіус'),'r2':('m','кінцевий радіус'),'mu':('m^3 s^-2','GM зорі')},{'r1':AU,'r2':1.523679*AU,'mu':MU_SUN},'m^2 s^-2','Різниця швидкостей на Hohmann орбіті; /1e6 дає km^2/s^2. Не крива вантажопідйомності.'),
    ('rocket_delta_v','delta_v=Isp*g0*ln(m0/mf)','Рівняння Ціолковського',{'Isp':('s','питомий імпульс'),'g0':('m s^-2','стандартне прискорення'),'m0':('kg','початкова маса'),'mf':('kg','кінцева маса')},{'Isp':320,'g0':9.80665,'m0':2000,'mf':1000},'m s^-1','Ідеальний імпульс; m0>=mf>0, без гравітаційних/аеродинамічних втрат.'),
    ('mission_mass','m_total=m_dry+m_payload+m_propellant+m_adapter','Масовий бюджет місії',{'m_dry':('kg','суха платформа без payload'),'m_payload':('kg','payload'),'m_propellant':('kg','паливо'),'m_adapter':('kg','адаптер')},{'m_dry':1500,'m_payload':500,'m_propellant':700,'m_adapter':100},'kg','Неперекривні складові. Perseverance 1025 kg уже містить прилади й MMRTG.'),
    ('signal_delay','tau=d/c','Одностороння геометрична затримка',{'d':('m','відстань')},{'d':AU},'s','Миттєва евклідова відстань; не retarded light-time чи двостороння відповідь.'),
    ('received_power','Pr=Pt*Gt*Gr*(lambda/(4*pi*d))^2','Ідеальний Friis link budget',{'Pt':('W','передана потужність'),'Gt':('1','лінійне підсилення передавача'),'Gr':('1','лінійне підсилення приймача'),'wavelength':('m','довжина хвилі'),'d':('m','дальність')},{'Pt':10,'Gt':100,'Gr':100,'wavelength':.036,'d':AU},'W','Далеке поле, LOS, без втрат. Не визначає bitrate без шуму, модуляції та Eb/N0.'),
    ('solar_power','P=S*area*eta*max(0,cos(theta))*dust','Енергія сонячної панелі',{'S':('W m^-2','потік'),'area':('m^2','площа'),'eta':('1','ККД'),'theta':('rad','кут до нормалі'),'dust':('1','частка після пилового ослаблення')},{'S':589,'area':2,'eta':.25,'theta':0,'dust':.7},'W','Умовна панель для дизайну місії, Perseverance використовує MMRTG. Не додавати атмосферні втрати двічі.'),
    ('slope','theta=atan(sqrt((dz/dx)^2+(dz/dy)^2))','Похил DEM',{'dz_dx':('1','градієнт за східним напрямком'),'dz_dy':('1','градієнт за північним напрямком')},{'dz_dx':.1,'dz_dy':0},'rad','Центральна різниця, однаковий горизонтальний/вертикальний метр, маскувати nodata.'),
    ('rover_force','F=m*a+m*g*(sin(theta)+Crr*cos(theta))','Тягове зусилля вздовж маршруту',{'m':('kg','повна маса'),'g':('m s^-2','гравітація'),'theta':('rad','поздовжній похил; підйом>0'),'Crr':('1','коефіцієнт кочення'),'a':('m s^-2','прискорення')},{'m':1025,'g':3.71,'theta':math.radians(5),'Crr':.04,'a':0},'N','Ігрова модель твердого покриття, без буксування й просідання; Crr потребує калібрування.'),
    ('rover_energy','E=max(0,F*s)/eta+P_aux*t','Енергія проїзду',{'F':('N','тягове зусилля'),'s':('m','довжина 3D шляху'),'eta':('1','ККД приводу'),'P_aux':('W','допоміжні системи під час руху'),'t':('s','тривалість')},{'F':500,'s':100,'eta':.5,'P_aux':120,'t':100/.03},'J','Ділянки маршруту сумувати окремо; без рекуперації. J/3600=Wh; не чистий розряд батареї.'),
    ('battery_delta','dE=eta_c*(P_gen-P_load)*t if surplus else (P_gen-P_load)*t/eta_d','Зміна запасу батареї',{'P_gen':('W','генерація'),'P_load':('W','усі навантаження'),'t':('s','крок'),'eta_c':('1','ККД заряду'),'eta_d':('1','ККД розряду')},{'P_gen':110,'P_load':160,'t':3600,'eta_c':.95,'eta_d':.95},'J','Потім clamp E до [reserve,capacity], врахувати недообслуговане навантаження. Не продовжувати дію при порожній батареї.'),
    ('data_balance','D_next=max(0,D+Q-rate*t)','Баланс даних за крок',{'D':('bit','буфер до кроку'),'Q':('bit','створені дані'),'rate':('bit s^-1','ефективний bitrate лише під час сеансу'),'t':('s','час сеансу')},{'D':200e6,'Q':50e6,'rate':1e6,'t':120},'bit','Обмежити передавання доступним буфером; окремо показати overflow понад capacity. 1 MB=8 Mbit.'),
    ('drag','F_drag=0.5*rho*v^2*Cd*area','Опір у спрощеному EDL',{'rho':('kg m^-3','локальна густина газу'),'v':('m s^-1','швидкість відносно газу'),'Cd':('1','коефіцієнт опору'),'area':('m^2','лобова площа')},{'rho':.02,'v':100,'Cd':1.5,'area':10},'N','Режимно-залежний Cd; без нагріву, Mach, підйому чи повної валідації посадки.'),
    ('hill_radius','R_H=((a1+a2)/2)*((m1+m2)/(3*Mstar))^(1/3)','Взаємний радіус Hill',{'a':('m','середня велика піввісь сусідів'),'m1':('kg','маса внутрішньої планети'),'m2':('kg','маса зовнішньої планети'),'Mstar':('kg','маса зорі')},{'a':1.1*AU,'m1':EARTH_MASS,'m2':EARTH_MASS,'Mstar':MU_SUN/G},'m','Перевіряти gap=outer_periapsis-inner_apoapsis >=10*R_H. Консервативна евристика, не доведення довготривалої стабільності.'),
    ('visual_orbit','r_view=scale*ln(1+a/a0)','Стиснення орбіт для огляду',{'a':('m','фізична піввісь'),'scale':('view_unit','масштаб сцени'),'a0':('m','опорна відстань')},{'a':AU,'scale':20,'a0':.1*AU},'view_unit','Лише оглядова сцена. Рух і delta-v рахувати в SI, не на стиснених відстанях.'),
    ('visual_radius','R_view=scale*sqrt(R/R0)','Збільшення видимих планет',{'R':('m','реальний радіус'),'scale':('view_unit','видимий радіус опорного тіла'),'R0':('m','опорний радіус')},{'R':EARTH_RADIUS,'scale':.5,'R0':EARTH_RADIUS},'view_unit','Масштаб радіусів незалежний від орбіт; явно позначити в UI.'),
    ('constant_acceleration','s=v0*t+0.5*a*t^2','Прямолінійний рух на одному кроці',{'v0':('m s^-1','початкова швидкість'),'a':('m s^-2','стале прискорення'),'t':('s','крок')},{'v0':.02,'a':.001,'t':1},'m','Стала a на кроці; обмежити v швидкістю профілю, повторно рахувати крок при досягненні межі.'),
    ]
    out=[]
    for id,expression,purpose,variables,inputs,unit,limits in specs:
        out.append({'id':id,'expression':expression,'purpose_uk':purpose,'variables':{k:{'unit':u,'meaning_uk':s} for k,(u,s) in variables.items()},'output_unit':unit,'example':{'inputs':inputs,'expected':check_finite(FORMULAS[id](**inputs)),'relative_tolerance':1e-10},'domain_and_limits_uk':limits,'source':PARAMETERS if id in ['period','vis_viva','escape_speed','signal_delay'] else DERIVATION,'derivation':id})
    write('data/physics/formulas.json',{'schema_version':'1.0','constant_catalog':'data/physics/physical_constants.json','formulas':out})

def planet_models():
    types=[]
    for id,bounds,label,atmo,appearance,landing in [
      ('rocky_candidate',[.3,1.6],'Кам’яниста кандидатна','none_or_thin_co2','cratered basalt / iron oxides; procedural, not inferred from radius',True),
      ('sub_neptune',[1.6,4],'Субнептун','h2_he','hazy desaturated envelope; procedural',False),
      ('ice_giant_candidate',[4,8],'Крижаний гігант кандидатний','h2_he','cyan/blue bands are artistic, not measured composition',False),
      ('gas_giant',[8,14],'Газовий гігант','h2_he','bands and storms; optional rings are art',False)]:
        types.append({'id':id,'name_uk':label,'radius_earth_range':bounds,'interval':'lower-inclusive upper-exclusive; last upper-inclusive','classification_status':'game_radius_class_not_unique_composition','mass_radius_rule':'select joint pair from mass_radius_anchors.json; never draw mass and radius independently','atmosphere_preset':atmo,'surface_landing_supported':landing,'visual_rule':appearance})
    write('data/planets/planet_types.json',{'schema_version':'1.0','source_ids':['nasa_exoplanet_archive','nasa_emac_exovista_dec21'],'types':types})
    gp=copy.deepcopy(CONFIG['generation'])
    gp.update({'schema_version':'1.0','status':'game_model_informed_by_empirical_and_synthetic_data','rng':{'algorithm':'xorshift32','seed_type':'uint32','zero_seed_maps_to':1831565813,'uniform':'next_uint32 / 4294967296; [0,1)','stream_version':1},'class_weights':{'rocky_candidate':.35,'sub_neptune':.30,'ice_giant_candidate':.20,'gas_giant':.15},'weights_status':'balanced game assumptions, not unbiased observed occurrence','star_model':{'status':'main_sequence_approximation','luminosity_exponent':4,'radius_exponent':.8,'temperature_rule':'derive from L and R via Stefan-Boltzmann','multiplicity':'single star only'},'sampling':{'radii_and_masses':'paired ExoVista anchors, no independent scatter','eccentricity':'uniform [0,e_max] (game choice)','orientation':'one isotropic common plane; node uniform 0..2pi; planets coplanar','phase':'mean anomaly uniform 0..2pi; solve elliptic Kepler equation','spin':'log-uniform bounded by breakup safety; cosmetic tide-lock switch is not a tidal evolution solver'},'rejection':{'max_planet_attempts':128,'max_system_attempts':16,'fail':'throw explicit generation error; never silently remove planets'},'atmosphere_rules':'Atmosphere pressure/composition are illustrative presets, not inferred observations. Radius class cannot establish habitability or oxygen.','source_ids':['nasa_exoplanet_archive','nasa_emac_exovista_dec21']})
    write('data/planets/generation_parameters.json',gp)
    presets=[
      {'id':'none','surface_pressure_pa':0,'mole_fractions':{},'molar_mass_kg_mol':None,'status':'game_assumption'},
      {'id':'thin_co2','surface_pressure_pa':610,'mole_fractions':{'CO2':.951,'N2':.0259,'Ar':.0194,'O2':.0016,'CO':.0006,'other':.0015},'molar_mass_kg_mol':.04334,'status':'Mars_like_illustrative_composition; pressure rounded reference, not Jezero weather','source':'https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html'},
      {'id':'h2_he','reference_pressure_pa':1e5,'surface_pressure_pa':None,'mole_fractions':{'H2':.86,'He':.14},'molar_mass_kg_mol':.002294,'status':'illustrative_H2_He_envelope','note':'1 bar is an arbitrary display level, no solid surface or measured abundance'},
      {'id':'n2_co2','surface_pressure_pa':1e5,'mole_fractions':{'N2':.9,'CO2':.1},'molar_mass_kg_mol':.029613,'status':'game_assumption','note':'Optional authored rocky world; not assigned by random generator and not claimed habitable'},
    ]
    write('data/planets/atmospheres.json',{'schema_version':'1.0','fraction_basis':'mole/volume, not mass','status':'illustrative_presets_not_exoplanet_measurements','source_ids':['nasa_mars_facts'],'presets':presets})

def missions():
    for name in ['components','launchers','orbits','edl','relay_plans']:
        data=copy.deepcopy(read(f'data/catalogs/{name}.json'))
        data['package_note']='Snapshot reference with per-field units in names; null means unavailable, never zero. See docs/PHYSICS.md and source URLs.'
        if name=='edl':
            for phase in data['phases']:
                if phase['phase']=='peak_heating':
                    phase['time_from_entry_s']=75
                    phase['source_status']='NASA launch press kit p.27, approximate peak heating time'
                if phase['phase']=='powered_descent':
                    phase['velocity_m_s']=306/3.6
                    phase['velocity_basis']='306 km/h / 3.6 = 85 m/s; corrected raw catalog unit error (306 was km/h, not m/s)'
        if name=='components':
            for x in data['components']:
                if x['id']=='rover_batteries':
                    x['mass_kg']=26.5
                    x['capacity_ah_each']=43
                    x['confidence']='published pair mass and count; approximate per-battery Ah; usable Wh unknown'
                    x['source_additional']='https://www.jpl.nasa.gov/news/press_kits/mars_2020/download/mars_2020_launch_press_kit.pdf#page=38'
                    x['limitations']=['Battery-pair mass 26.5 kg and ~43 Ah each verified in press kit p.38. Usable Wh not specified; capacity_wh stays null.']
                x['status']='unavailable' if x['confidence'].startswith('not_') else 'published_or_described_reference'
        if name=='launchers':
            data['launchers'][0]['flight_reference']['status']='NASA/ULA launch press-kit nominal profile for the flown mission; not measured injection telemetry or a capability curve'
            data['launchers'][0]['flight_reference']['spacecraft_payload_mass_kg']=None
            data['launchers'][0]['flight_reference']['mass_note']='Raw catalog 3893 kg is not substantiated for Mars 2020 in the cited press kit; withheld (likely mission conflation)'
            data['launchers'][0]['confidence']='Nominal C3 verified in JPL/ULA press kit; launch mass and exact LEO capability withheld; no C3 payload curve'
            data['launchers'][0]['payload_to_leo_kg']=None
            data['launchers'][0]['leo_note']='Earlier local catalog quoted 17410 kg; exact primary-source configuration curve not verified in this pass, withheld from operational capability checks'
            data['launchers'][1]['source_additional']='https://public.ksc.nasa.gov/lspeducation/spacex/'
        if name=='orbits':
            data['transfer_options'][1]['status']='Mars 2020 historical mission, nominal C3 in launch press kit; not measured injection telemetry'
            data['transfer_options'][1]['model']='historical launch example with nominal press-kit injection parameters'
            data['transfer_options'][1]['spacecraft_mass_at_launch_kg']=None
            data['transfer_options'][1]['mass_note']='3893 kg in local catalog was not verified for this mission; no substitute invented'
            row=data['transfer_options'][0]
            row['departure_c3_km2_s2']=FORMULAS['departure_c3'](AU,1.523679*AU,MU_SUN)/1e6
            row['departure_excess_speed_km_s']=math.sqrt(row['departure_c3_km2_s2'])
            row['transfer_duration_days']=FORMULAS['hohmann_time'](AU,1.523679*AU,MU_SUN)/86400
        write(f'data/missions/{name}.json',data)
    write('data/missions/game_scenario.json',{'schema_version':'1.0','id':'jezero-training-v1','status':'game_assumption','reference_epoch':'2026-11-14','mission_duration_sols':30,'starting_energy_fraction':.8,'minimum_reserve_fraction':.1,'relay':{'orbiter_id':'mro','contacts_per_sol':2,'duration_s':480,'net_rate_bit_s':350000,'timing':'scheduled game events, not predicted overflights','data_per_contact_bit':168000000},'mass_budget':{'margin_fraction':.2,'rule':'apply to non-overlapping dry mass estimate only; require separate propulsion/EDL estimates'},'launcher_compatibility':{'mode':'reference_only','unknown_curve_action':'indeterminate','historical_atlas_reference_mass_kg':None,'historical_c3_m2_s2':14490000,'rule':'Do not interpolate from a single historic flight; Falcon Heavy Mars payload lacks specified C3.'},'edl':{'mode':'scripted_reference_sequence','unsupported_payload_action':'indeterminate; no safe-landing result'},'power':{'solar_array_area_m2':2,'solar_efficiency':.25,'dust_transmission':.7,'note':'optional hypothetical solar design, not Perseverance hardware'}})

def rover():
    profiles=[]
    for id,mass,speed,energy,buf,slope,instruments in [
      ('scout',900,.04,1600,2048,15,['mastcam_z','meda']),
      ('science',1025,.03,2400,4096,15,['mastcam_z','meda','supercam','pixl','sherloc_watson','rimfax']),
      ('cargo',1200,.02,3200,8192,12,['mastcam_z','meda','rimfax'])]:
        profiles.append({'id':id,'status':'game_assumption_pending_SASHA_MISHA_balance','total_mass_kg':mass,'max_speed_m_s':speed,'battery_capacity_wh':energy,'buffer_mbit':buf,'operational_slope_limit_deg':slope,'generation_w':110,'drive_efficiency':.5,'rolling_resistance':.04,'idle_power_w':80,'drive_aux_power_w':120,'battery_charge_efficiency':.95,'battery_discharge_efficiency':.95,'max_traction_coefficient':.6,'body_dimensions_m':[3,2.7,2.2],'wheel_diameter_m':.525,'instrument_ids':instruments,'note':'Whole vehicle mass includes listed instruments; no NASA variant claim. No new wheel geometry implied.'})
    write('data/rover/rover_specs.json',{'schema_version':'1.0','source_ids':['nasa_perseverance_rover_components'],'reference':{'id':'perseverance','status':'published_reference','total_mass_kg':1025,'dimensions_length_width_height_m':[3,2.7,2.2],'wheel_count':6,'wheel_diameter_m':.525,'max_flat_hard_ground_speed_m_s':152/3600,'avoid_tilt_above_deg':30,'static_tip_resistance_deg':45,'mmrtg_initial_electric_w':110,'mmrtg_mass_kg':45,'battery_count':2,'battery_capacity_wh':None,'battery_capacity_status':'usable Wh not verified; earlier audit 2408 Wh requires a voltage assumption','battery_mass_kg':26.5,'battery_capacity_ah_each':43,'peak_power_w_approx':900,'battery_source':'https://www.jpl.nasa.gov/news/press_kits/mars_2020/download/mars_2020_launch_press_kit.pdf#page=38','source':ROVER},'motion_model':'quasi-static force and positive traction work + auxiliary load; no regeneration; terrain sampled every <=10 m','route_contract':{'id':'caller-defined string','terrain_id':'jezero_landing_10km','waypoints':'array of [x,y,z] in meters, x east/y up/z south','step_m_max':10,'out_of_bounds_action':'block','nodata_action':'block','on_caution':'require manual reroute or override; cannot certify safety'},'profiles':profiles})

if __name__=='__main__':
    for fn in [constants,formulas,planet_models,missions,rover]:fn();print(fn.__name__,'OK')
