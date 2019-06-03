# the models require the lme4 package, version 1.1-19
# require(devtools)
# install_version("lme4", version = "1.1-19", repos = "http://cran.us.r-project.org")
library(lme4);
library(optparse)

option_list = list(
  make_option(c("--booked"), type="character", default=NULL, 
              help="Dataset for model probability of booking a truck (filepath)", metavar="character"),
  make_option(c("--cogs"), type="character", default=NULL, 
              help="Dataset for model buy cost given successful booking (filepath)", metavar="character")
); 

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

if (is.null(opt$booked)){
  print_help(opt_parser)
  stop("--booked argument must be supplied", call.=FALSE)
}
if (is.null(opt$cogs)){
  print_help(opt_parser)
  stop("--cogs argument must be supplied", call.=FALSE)
}

df_booked <- read.csv(file=opt$booked, header=TRUE, sep=",")
df_cogs <- read.csv(file=opt$cogs, header=TRUE, sep=",")

#model probability of booking a truck
mod_booked <- glmer(Booked ~ (1|AssignmentType) + (1|RepOriginMarketId) + (1|RepDestinationMarketId) + (1|RepLaneId)
                    , data=df_booked
                    , family="binomial"
                    , nAGQ = 0
                    , control=glmerControl(optimizer="nloptwrap", calc.derivs = FALSE))

save(mod_booked,file="mod_booked.Rda")

#model buy cost given successful booking
mod_cogs <- 
  lmer(logCOGS ~ (1 + logDAT + logMiles|LaneId) + (1|RepLaneId)
                 , data=df_cogs
                 , control=lmerControl(optimizer="nloptwrap", calc.derivs = FALSE)
     , weights = Wt)

save(mod_cogs,file="mod_cogs.Rda")
