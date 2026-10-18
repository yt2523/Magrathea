#include "EOS.h"
double rho_eps_rel=1E-11;
double T_eps_rel=1E-11;
bool verbose=false;
int main(){
  gsl_set_error_handler_off();
  double p[][2]={{0,6},{5,18},{14,0},{33,5.537},{34,0.0305}};
  EOS eos("Water vdW probe",p,5);
  cout << std::setprecision(17);
  for(double guess: {-1.0,1E-6,2.7E-5,5.4E-5,0.4}) {
    double rho=eos.density(5E4,400,guess);
    cout << "guess=" << guess << " rho=" << rho << " pressure_GPa=" << eos.Press(rho,400) << endl;
  }
}
