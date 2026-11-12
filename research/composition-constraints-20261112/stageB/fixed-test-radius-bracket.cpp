#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#ifdef USE_DOMAIN_BRACKET
#include "radius_bracket.h"
#else
struct RadiusSample {double radius,value;bool valid;};
struct RadiusBracket {bool found=false,ambiguous=false; double lo=0,hi=0;int trials=0;std::string reason;};
static RadiusBracket find_radius_bracket(const std::function<double(double)>& f,double guess,int cap=12){RadiusBracket r; r.lo=.8*guess;r.hi=1.2*guess;double a=f(r.lo),b=f(r.hi);r.trials=2;r.found=std::isfinite(a)&&std::isfinite(b)&&a*b<=0;return r;}
#endif
static int failures=0;
static void req(bool x,const char* m){if(!x){std::cerr<<"FAIL "<<m<<"\n";++failures;}}
int main(){
 const double nan=std::numeric_limits<double>::quiet_NaN();
 auto a=find_radius_bracket([&](double x){return x<.85?nan:x-1.03125;},1.,12);
 req(a.found&&!a.ambiguous,"invalid low initial trial must not preclude later valid bracket");
 if(a.found)req(a.lo<a.hi&&a.lo>=.85&&a.lo<=1.03125&&a.hi>=1.03125,"finite enclosing endpoints");
 auto b=find_radius_bracket([&](double x){return x>1.3?x-1.:nan;},1.,12);req(!b.found,"true domain shortfall not fabricated sign");
 auto c=find_radius_bracket([&](double x){return x>.95&&x<1.05?nan:x-1.;},1.,12);req(!c.found,"known invalid hole cannot be crossed as valid bracket");
 auto d=find_radius_bracket([](double x){return (x-.925)*(x-1.075);},1.,12);req(!d.found&&d.ambiguous,"multiple sampled brackets reported ambiguous");
 auto e=find_radius_bracket([](double x){return x+1.;},1.,12);req(!e.found,"same-sign no bracket");
 auto f=find_radius_bracket([&](double){return nan;},1.,12);req(!f.found,"all invalid bounded failure");
 for(auto q:{a,b,c,d,e,f})req(q.trials<=12,"strict trial budget");
 if(!failures)std::cout<<"PASS bounded radius domain fixtures\n";
 return failures?1:0;
}
