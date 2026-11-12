// Fixed acceptance: EOS continuity and thermal law, no planetary integrations.
#define main native_main_for_test
#include "src/main.cpp"
#undef main
#include <cassert>
int derivs_m2(double,const double[],double[],void*);
int derivs_m3(double,const double[],double[],void*);
static void need(bool x,const char*why){if(!x)throw std::runtime_error(why);}
int main(){try{
 gsl_set_error_handler_off();configure_prescribed_hhe_audit();
#ifdef TEST_UNIFIED_HHE100
 auto select=find_phase_gas_hhe_iso_adiabatic100;
#else
 auto select=find_phase_HHe_tabulated;
#endif
 EOS* low=select(1e8*(1-1e-8),350);EOS* high=select(1e8,350);
 need(low&&high,"selector returns phases");
 double a=low->density(1e8,350,-1),b=high->density(1e8,350,-1);
 double rel=std::abs(a/b-1);std::cout<<std::setprecision(17)<<"COMMON_STATE_DENSITY_RELATIVE "<<rel<<"\n";
 need(std::isfinite(a)&&std::isfinite(b)&&rel<=1e-12,"density changes at thermal switch");
#ifdef TEST_UNIFIED_HHE100
 need(low==Gas_hhe_iso100&&high==Gas_hhe,"unified selector identities");
 need(low->thermal_code()==0&&high->thermal_code()==10,"only thermal law differs");
 need(Gas_hhe->thermal_code()==10,"shared original gas not mutated");
 need(find_phase_HHe_tabulated(1e7,350)==Gas_iso,"legacy selector unchanged");
 need(select(0,350)==nullptr&&select(1e8,0)==nullptr&&select(std::numeric_limits<double>::infinity(),350)==nullptr,"invalid selector inputs");
 for(double T:{350.,700.,1200.})for(double P:{1e5,1e7,1e8,1e9}){
  double x=low->density(P,T,-1),y=Gas_hhe->density(P,T,-1);
  need(std::isfinite(x)&&std::isfinite(y)&&std::abs(x/y-1)<=1e-12,"same density table across states");
 }
 for(double P:{1e8*(1-1e-8),1e8*(1+1e-8)}){
  EOS* phase=select(P,350);mass_params par;par.x={-1.,double(phase->thermal_code())};par.M={1.,0.,1.,.01};par.Phase=phase;par.tp=nullptr;par.tp_gas=false;par.tp_diagnostics=nullptr;
  double y[3]={2*RE,P,350},out[3];need(derivs_m2(.1*ME,y,out,&par)==GSL_SUCCESS,"outside-in derivative");
  double guess=phase->density(P,350,-1);double expected=P<1e8?0:Gas_hhe->dTdP_S(P/1e10,350,guess)*out[1]/1e10;
  need(std::isfinite(out[2])&&std::abs(out[2]-expected)<=1e-12*std::max(1e-300,std::abs(expected)),"outside-in thermal law");
  need(derivs_m3(.1*ME,y,out,&par)==GSL_SUCCESS,"inside-out derivative");
  guess=phase->density(P,350,-1);expected=P<1e8?0:Gas_hhe->dTdP_S(P/1e10,350,guess)*out[1]/1e10;
  need(std::isfinite(out[2])&&std::abs(out[2]-expected)<=1e-12*std::max(1e-300,std::abs(expected)),"inside-out thermal law");
 }
 need(!std::isfinite(low->density(1.,350,-1))&&!std::isfinite(high->density(1.,350,-1)),"both reject outside table");
 need(select(std::numeric_limits<double>::quiet_NaN(),350)==nullptr&&select(1e8,std::numeric_limits<double>::infinity())==nullptr,"nonfinite selector guards");
 for(EOS* e:{low,high}){
  need(!e->table_domain_contains(1e5,99)&&!std::isfinite(e->density(1e5,99,-1)),"temperature domain rejection");
  need(!e->table_domain_contains(1e24,350)&&!std::isfinite(e->density(1e24,350,-1)),"high pressure rejection");
 }
 double near_lo=low->density(1e8*(1-1e-8),350,-1),near_hi=high->density(1e8*(1+1e-8),350,-1);
 need(std::abs(near_hi/near_lo-1)<=1e-6,"density near thermal switch continuous");
 auto opts=tp_settings::validate(0,1,0,1,.01,0,0,0,"gas_hhe_iso_adiabatic100",false,"",".");need(!opts.enabled,"no external TP enabled");
 bool bad=false;try{tp_settings::validate(0,1,0,1,.01,0,0,0,"gas_hhe_iso_adiabatic100",true,"\"x.csv\"",".");}catch(...){bad=true;}need(bad,"reject external TP");
 bad=false;try{tp_settings::validate(3,1,0,1,.01,0,0,0,"gas_hhe_iso_adiabatic100",false,"",".");}catch(...){bad=true;}need(bad,"reject unreviewed modes");
 std::cout<<"UNIFIED_HHE100_UNIT_PASS\n";
#endif
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
