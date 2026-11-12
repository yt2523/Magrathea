#include "radius_bracket.h"
#include <iostream>
int main(){int fail=0;for(double root:{1.0,.95}){auto r=find_radius_bracket([&](double x){return x-root;},1.,12);if(!r.found||r.ambiguous){++fail;std::cerr<<"FAIL exact root "<<root<<"\n";}}auto r=find_radius_bracket([](double x){return 1.4-x;},1.,12);if(!r.found){++fail;std::cerr<<"FAIL reverse slope upper root\n";}return fail?1:0;}
