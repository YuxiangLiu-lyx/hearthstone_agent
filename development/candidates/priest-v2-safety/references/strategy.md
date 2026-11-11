# Control Priest strategy

The policy starts from the local opposing Control Priest. It preserves immediate
lethal priority and specializes permanent theft, removal, health buffs, healing and
resource preservation. Replan from current legal templates after every action.

Scarlet Subjugator reduces a four-Attack minion to Cabal's two-Attack threshold;
it also enables Shadow Word: Pain on four- or five-Attack targets. Count mana and
all required board slots before enabling a steal. Cabal itself consumes a slot.
Mind Control removes an opposing threat and retains its body without activating
its deathrattle. Natalie Seline destroys the target and gains its current Health.

Temporary Shadow Madness theft is valued for same-turn exchanges. Public own-turn
history identifies the borrowed minion; spend it on a useful trade and avoid healing
or permanently buffing a body that will return. If it dies, its deathrattle belongs
to the controller at death. Frozen or cannot-attack targets are not assumed usable.
Faceless chooses a valuable public body; copied unknown effects use the inherited
generic legal policy, without assuming hidden card identities.

Health buffs and healing are more valuable when they change a trade from a loss into
a surviving kill. Holy Nova includes friendly healing as well as enemy damage. Ruin
counts casualties on both boards. Keep resources while clearly ahead, and prioritize
hero healing when visible pressure or known fatigue is lethal. Thoughtsteal is
resource generation; it does not remove cards from the opponent's deck and cannot
produce cards from an empty deck. No future copied card is assumed in a lethal proof.

Important hs-arena 0.2.2 differences, checked against actual engine execution:
Power Word: Shield costs zero and does not draw. Holy Nova costs four and hits enemy
minions, not the enemy hero. Thoughtsteal costs two. Shadow Madness costs three.
Power Infusion's printed text is +2/+6, but this packaged engine executes +2/+2;
the policy uses the executed effect. Northshire Cleric, Auchenai Soulpriest, Divine
Spirit and several familiar legendary cards are outside the permitted pool.

The small buff-lethal search handles already-legal face attacks and up to three
Shield/Inner Fire/Power Infusion plays, abstaining on secrets and unsupported own
triggers. Coordinated exchanges use at most three actions/1,600 nodes with an explicit
supported-effect subset. Neither is an exhaustive game tree. No engine/RNG/hidden
opponent state is accessed by the submitted skill. The two-second subprocess watchdog
and current-state action validator protect the official relay protocol.
