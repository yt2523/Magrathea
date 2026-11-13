#include "radius_bracket.h"
#include <iostream>
#include <limits>
#include <string>
int main(int argc,char**argv){if(argc>1){double z=std::numeric_limits<double>::denorm_min();auto r=find_radius_bracket([&](double x){return x==2*z?-1.:1.;},3*z,12);return r.found?1:0;}const double nan=std::numeric_limits<double>::quiet_NaN();auto r=find_radius_bracket([&](double x){return ((x>.85&&x<.95)||(x>1.05&&x<1.15))?nan:x-1.;},1.,12);for(auto a:r.samples)if(!a.valid&&r.found&&r.lo<a.radius&&a.radius<r.hi){std::cerr<<"FAIL zero bracket crossed known invalid sample\n";return 1;}return 0;}
