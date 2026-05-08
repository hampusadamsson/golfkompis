<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import {
		Accordion,
		AccordionContent,
		AccordionItem,
		AccordionTrigger
	} from '$lib/components/ui/accordion';
	import SearchIcon from '@lucide/svelte/icons/search';
	import CalendarCheckIcon from '@lucide/svelte/icons/calendar-check';
	import UsersIcon from '@lucide/svelte/icons/users';
	import TargetIcon from '@lucide/svelte/icons/target';
	import RadioTowerIcon from '@lucide/svelte/icons/radio-tower';
	import MousePointerClickIcon from '@lucide/svelte/icons/mouse-pointer-click';
	import ClockIcon from '@lucide/svelte/icons/clock';
	import CheckCircleIcon from '@lucide/svelte/icons/check-circle';
	import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
	import GlobeIcon from '@lucide/svelte/icons/globe';
	import BellRingIcon from '@lucide/svelte/icons/bell-ring';
	import AlarmClockIcon from '@lucide/svelte/icons/alarm-clock';
	import SparklesIcon from '@lucide/svelte/icons/sparkles';

	const trustItems = [
		{ icon: GlobeIcon, value: 'Alla GIT-klubbar', label: 'Alla Min Golf-anslutna golfbanor' },
		{ icon: BellRingIcon, value: 'Bevaka starttider', label: 'Sök och köbevaka parallellt' },
		{ icon: AlarmClockIcon, value: 'Dygnet runt', label: 'Hittar avbokade tider åt dig' },
		{ icon: SparklesIcon, value: 'Gratis beta', label: 'Inget kreditkort krävs' }
	];

	const features = [
		{
			icon: SearchIcon,
			title: 'Hitta lediga starttider',
			primary: true,
			description:
				'Sök lediga golftider på flera klubbar samtidigt — Bro Hof, Ullna, Kungsängen och alla andra GIT-anslutna banor. Filtrera på tid, datum och spelare och boka direkt.'
		},
		{
			icon: CalendarCheckIcon,
			title: 'Håll koll på dina golfbokningar',
			primary: false,
			description:
				'Se kommande golftider och avboka med ett klick. All bokningshistorik på en sida — alltid uppdaterad mot Min Golf.'
		},
		{
			icon: UsersIcon,
			title: 'Spela med kompisar',
			primary: false,
			description: 'Se kompisars handicap och spelhistorik — golf är roligare med rätt sällskap.'
		}
	];

	const howItWorks = [
		{
			icon: TargetIcon,
			step: '1',
			title: 'Välj klubbar och tidsfönster',
			description:
				'Välj en eller flera GIT-anslutna klubbar, ett datum och ett önskat tidsfönster. Ange hur många spelare det gäller.'
		},
		{
			icon: RadioTowerIcon,
			step: '2',
			title: 'Vi bevakar Min Golf åt dig',
			description:
				'Golfkompis kontrollerar automatiskt lediga starttider — flera gånger per minut — dygnet runt tills en tid öppnar sig.'
		},
		{
			icon: MousePointerClickIcon,
			step: '3',
			title: 'Boka starttiden med ett klick',
			description:
				'När en matchande starttid dyker upp ser du den direkt och får e-post. Boka med ett klick — utan att lämna Golfkompis.'
		}
	];

	const faqs = [
		{
			question: 'Hur hittar jag lediga golftider på populära klubbar?',
			answer:
				'Med Golfkompis söker du lediga starttider på flera klubbar i ett enda steg. Välj till exempel Bro Hof Slott, Ullna GK och Kungsängen GC på en gång — Golfkompis hämtar tillgängliga tider från Min Golf parallellt och visar dem samlat. Ingen inloggning på Min Golf krävs varje gång.'
		},
		{
			question: 'Kan jag bevaka avbokade tider på Bro Hof, Ullna eller Kungsängen?',
			answer:
				'Ja. Ställ dig i kö för valfri GIT-ansluten klubb — inklusive Bro Hof Slott, Ullna GK, Kungsängen GC och Österåker GK. Golfkompis bevakar Min Golf automatiskt och meddelar dig via e-post så fort en avbokad starttid som matchar dina kriterier dyker upp.'
		},
		{
			question: 'Vad är skillnaden mellan Min Golf-appen och Golfkompis?',
			answer:
				'Min Golf är SGF:s officiella system som alla klubbar och spelare använder för bokningar. Golfkompis är ett komplement som läggs ovanpå: du kan söka på flera klubbar simultant, bevaka fullbokade tider i kö och få e-postavisering vid match — funktioner som saknas i Min Golf-appen. Golfkompis är inte anslutet till SGF.'
		},
		{
			question: 'Hur fungerar köbevakning för eftertraktade helgmorgnar?',
			answer:
				'Välj datum (t.ex. lördag), sätt tidsfönstret till 07:00–11:00 och lägg till de klubbar du vill spela på. Golfkompis lägger en aktiv bevakning och kontrollerar Min Golf upprepade gånger. Så fort en avbokning sker på den valda morgonen matchas du och får ett e-postmeddelande — vanligtvis inom minuter från att en tid öppnas.'
		},
		{
			question: 'Är det säkert att koppla mitt Min Golf-konto?',
			answer:
				'Golfkompis loggar in på Min Golf i ditt namn med de uppgifter du anger — precis som du skulle göra själv. Vi lagrar inga lösenord i klartext. Kopplingen är frivillig och du kan ta bort den när som helst under Konto.'
		},
		{
			question: 'Hur ofta kontrolleras lediga starttider?',
			answer:
				'Köbevakningarna kontrolleras automatiskt med korta intervall. Du kan se exakt hur många kontroller som gjorts och när senaste kontrollen skedde direkt i appen. Observera att Min Golf har hastighetsbegränsning — undvik att skapa onödigt många parallella bevakningar, eftersom överdriven användning kan leda till att ditt konto tillfälligt blockeras av Min Golf.'
		},
		{
			question: 'Kan jag köa för flera datum och banor samtidigt?',
			answer:
				'Ja. Du kan ha flera aktiva köbevakningar igång parallellt — olika datum, olika klubbar, olika tidsfönster. Varje bevakning är oberoende och matchas separat. Tänk på att hålla antalet rimligt för att inte trigga Min Golfs hastighetsbegränsning.'
		},
		{
			question: 'Vad händer när en starttid matchas?',
			answer:
				'Du får ett e-postmeddelande så fort en matchande starttid hittas. Bevakningen får även statusen "Matchad" och de lediga tiderna visas direkt i din kölista. Du bokar manuellt med ett klick — Golfkompis bokar aldrig utan din bekräftelse.'
		},
		{
			question: 'Kostar det något?',
			answer:
				'Golfkompis är gratis under betaperioden. Skapa ett konto och testa utan att ange betaluppgifter.'
		}
	];

	// Mock queue entries for the showcase
	const mockQueues = [
		{
			status: 'active',
			statusLabel: 'Aktiv',
			date: 'Lördag 12 maj',
			window: '07:00 – 11:00',
			spots: 2,
			courses: ['Bro Hof Slott', 'Ullna GK', 'Kungsängen GC'],
			meta: 'Senast kontrollerad: 12 sek sedan · 47 kontroller'
		},
		{
			status: 'matched',
			statusLabel: 'Matchad',
			date: 'Söndag 13 maj',
			window: 'Hela dagen',
			spots: 4,
			courses: ['Österåker GK'],
			meta: '2 avbokade tider hittades — boka nu'
		},
		{
			status: 'active',
			statusLabel: 'Aktiv',
			date: 'Måndag 14 maj',
			window: '16:00 – 19:00',
			spots: 1,
			courses: ['Ekerum Golf', 'Lindö Park GK'],
			meta: 'Senast kontrollerad: 1 min sedan · 12 kontroller'
		}
	];

	// JSON-LD structured data
	const orgSchema = {
		'@context': 'https://schema.org',
		'@type': 'Organization',
		name: 'Golfkompis',
		url: 'https://golfkompis.se',
		logo: 'https://golfkompis.se/golf_logo.png',
		description:
			'Golfkompis hjälper svenska golfare hitta lediga starttider och bevaka avbokade golftider på Min Golf — sök flera GIT-anslutna klubbar samtidigt.'
	};

	const faqSchema = {
		'@context': 'https://schema.org',
		'@type': 'FAQPage',
		mainEntity: faqs.map((f) => ({
			'@type': 'Question',
			name: f.question,
			acceptedAnswer: {
				'@type': 'Answer',
				text: f.answer
			}
		}))
	};
</script>

<svelte:head>
	<title>Boka golftid & bevaka lediga starttider | Golfkompis</title>
	<meta
		name="description"
		content="Hitta lediga golftider på Min Golf, bevaka avbokade starttider och boka på flera klubbar samtidigt — Bro Hof, Ullna, Kungsängen och alla GIT-anslutna banor."
	/>
	<meta property="og:title" content="Boka golftid & bevaka lediga starttider | Golfkompis" />
	<meta
		property="og:description"
		content="Sök lediga golftider på flera klubbar på en gång. Bevaka avbokade starttider i kö och få e-post direkt när en tid öppnas."
	/>
	<meta property="og:image" content="/golf_logo.png" />
	<meta property="og:type" content="website" />
	<meta property="og:locale" content="sv_SE" />
	<meta name="theme-color" content="#ffffff" />
	{@html `<script type="application/ld+json">${JSON.stringify(orgSchema)}<\/script>`}
	{@html `<script type="application/ld+json">${JSON.stringify(faqSchema)}<\/script>`}
</svelte:head>

<!-- Hero -->
<section
	class="mx-auto flex max-w-5xl flex-col items-center gap-6 px-4 py-16 md:flex-row md:gap-12 md:py-24"
	aria-labelledby="hero-heading"
>
	<!-- Text column -->
	<div class="flex flex-1 flex-col items-center gap-6 text-center md:items-start md:text-left">
		<p class="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
			Smartare bokning för Min Golf
		</p>

		<h1 id="hero-heading" class="text-4xl font-bold tracking-tight sm:text-5xl">
			Boka golftid och bevaka lediga starttider
		</h1>

		<p class="max-w-md text-lg text-muted-foreground">
			Hitta lediga golftider på flera klubbar på en gång, bevaka avbokade starttider i kö och boka
			direkt — utan att jaga Min Golf-appen.
		</p>

		<div class="flex flex-wrap justify-center gap-3 md:justify-start">
			<Button size="lg" href="/register">Registrera dig gratis</Button>
			<Button size="lg" variant="outline" href="/login">Logga in</Button>
		</div>

		<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
		<a
			href="#queue"
			class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
		>
			Se hur köbevakning av starttider fungerar
			<ChevronDownIcon class="h-3.5 w-3.5" />
		</a>
	</div>

	<!-- Mascot column -->
	<div class="relative flex shrink-0 items-center justify-center md:w-80 lg:w-96">
		<div
			class="absolute inset-0 -z-10 scale-75 rounded-full bg-muted/60 blur-3xl"
			aria-hidden="true"
		></div>
		<img
			src="/golf_logo.png"
			alt="Golfkompis maskot — boka golftid och bevaka lediga starttider på Min Golf"
			width="1060"
			height="1100"
			class="-m-6 w-full max-w-xs sm:max-w-sm md:max-w-full"
			loading="eager"
			decoding="async"
			fetchpriority="high"
		/>
	</div>
</section>

<!-- Trust strip -->
<section class="border-y bg-muted/40 px-4 py-10" aria-label="Produktfakta">
	<div class="mx-auto grid max-w-5xl grid-cols-2 gap-6 text-center sm:grid-cols-4 sm:gap-4">
		{#each trustItems as item (item.value)}
			<div>
				<item.icon class="mx-auto mb-2 h-4 w-4 text-muted-foreground" />
				<p class="text-xl font-bold">{item.value}</p>
				<p class="mt-1 text-sm text-muted-foreground">{item.label}</p>
			</div>
		{/each}
	</div>
</section>

<!-- Features -->
<section id="features" class="px-4 py-20" aria-labelledby="features-heading">
	<div class="mx-auto max-w-5xl">
		<h2 id="features-heading" class="mb-12 text-center text-3xl font-semibold tracking-tight">
			Allt du behöver för att boka golftid smartare
		</h2>

		<div class="grid gap-6 sm:grid-cols-3">
			{#each features as feature (feature.title)}
				<Card
					class="transition-shadow hover:shadow-md {feature.primary
						? 'border-foreground/20'
						: ''}"
				>
					<CardHeader>
						<div class="mb-2 flex items-start justify-between">
							<div class="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10">
								<feature.icon class="h-5 w-5 text-primary" />
							</div>
							{#if feature.primary}
								<Badge variant="secondary" class="text-xs">Mest använt</Badge>
							{/if}
						</div>
						<CardTitle>{feature.title}</CardTitle>
					</CardHeader>
					<CardContent>
						<CardDescription>{feature.description}</CardDescription>
					</CardContent>
				</Card>
			{/each}
		</div>
	</div>
</section>

<!-- Queue showcase -->
<section id="queue" class="bg-muted/40 px-4 py-20" aria-labelledby="queue-heading">
	<div class="mx-auto max-w-5xl">
		<div class="mb-12 text-center">
			<h2 id="queue-heading" class="text-3xl font-semibold tracking-tight">
				Bevaka avbokade golftider — sätt dig i kö
			</h2>
			<p class="mx-auto mt-4 max-w-xl text-muted-foreground">
				Golfkompis bevakar Min Golf åt dig — på flera klubbar samtidigt, inom ditt valda
				tidsfönster. Så fort en avbokad starttid öppnas matchas du och får e-post direkt.
			</p>
		</div>

		<!-- How it works — explanation first -->
		<div class="mb-12">
			<h3 class="mb-8 text-center text-xl font-semibold">Hur köbevakningen fungerar</h3>
			<div class="grid gap-6 sm:grid-cols-3">
				{#each howItWorks as step (step.step)}
					<div class="flex flex-col items-center text-center">
						<div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
							<step.icon class="h-6 w-6 text-primary" />
						</div>
						<p class="mb-1 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
							Steg {step.step}
						</p>
						<h4 class="mb-2 font-semibold">{step.title}</h4>
						<p class="text-sm text-muted-foreground">{step.description}</p>
					</div>
				{/each}
			</div>
		</div>

		<!-- Mock booking form -->
		<div class="mb-10">
			<Card class="mx-auto max-w-xl">
				<CardHeader>
					<CardTitle class="text-base">Hitta eller bevaka lediga starttider</CardTitle>
					<CardDescription>Välj klubbar, datum och tidsfönster</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="space-y-4">
						<!-- Course chips -->
						<div>
							<p class="mb-2 text-xs font-medium text-muted-foreground">Klubbar</p>
							<div class="flex flex-wrap gap-2">
								{#each ['Bro Hof Slott', 'Ullna GK', 'Kungsängen GC', '+ 2 till'] as course}
									<Badge variant="secondary">{course}</Badge>
								{/each}
							</div>
						</div>
						<!-- Row: date + window + spots -->
						<div class="grid grid-cols-3 gap-3 text-sm">
							<div>
								<p class="mb-1 text-xs text-muted-foreground">Datum</p>
								<p class="rounded-md border bg-background px-2 py-1.5">2026-05-12</p>
							</div>
							<div>
								<p class="mb-1 text-xs text-muted-foreground">Tidsfönster</p>
								<p class="rounded-md border bg-background px-2 py-1.5">07:00 – 11:00</p>
							</div>
							<div>
								<p class="mb-1 text-xs text-muted-foreground">Spelare</p>
								<p class="rounded-md border bg-background px-2 py-1.5">2</p>
							</div>
						</div>
						<!-- Buttons -->
						<div class="flex gap-2 pt-1">
							<Button variant="outline" size="sm" class="flex-1">Sök lediga tider</Button>
							<Button size="sm" class="flex-1">Bevaka i kö</Button>
						</div>
					</div>
				</CardContent>
			</Card>
		</div>

		<!-- Parallel queue mocks — proof last -->
		<div class="mb-4">
			<h3 class="mb-6 text-center text-sm font-semibold text-muted-foreground">
				3 köbevakningar körs parallellt
			</h3>
			<div class="grid gap-3 lg:grid-cols-3">
				{#each mockQueues as q (q.date + q.window)}
					<Card
						class="transition-colors hover:border-foreground/40 {q.status === 'matched'
							? 'border-foreground/30'
							: ''}"
					>
						<CardContent class="flex flex-col gap-3 p-4">
							<div class="flex items-start justify-between gap-2">
								<div class="space-y-1.5 flex-1">
									<div class="flex flex-wrap items-center gap-x-2 gap-y-1">
										<span class="font-medium text-sm">{q.date}</span>
										<span class="text-xs text-muted-foreground">{q.window}</span>
									</div>
									<p class="text-xs text-muted-foreground">{q.spots} spelare</p>
								</div>
								<Badge variant={q.status === 'matched' ? 'default' : 'secondary'} class="shrink-0">
									{q.statusLabel}
								</Badge>
							</div>
							<div class="flex flex-wrap gap-1.5">
								{#each q.courses as course (course)}
									<Badge variant="outline" class="text-xs">{course}</Badge>
								{/each}
							</div>
							<div class="flex items-center justify-between gap-2">
								<div class="flex items-center gap-1.5 text-xs text-muted-foreground">
									{#if q.status === 'matched'}
										<CheckCircleIcon class="h-3.5 w-3.5 shrink-0 text-foreground" />
									{:else}
										<ClockIcon class="h-3.5 w-3.5 shrink-0" />
									{/if}
									{q.meta}
								</div>
								{#if q.status === 'matched'}
									<Button size="sm">Boka nu</Button>
								{/if}
							</div>
						</CardContent>
					</Card>
				{/each}
			</div>
		</div>
	</div>
</section>

<!-- FAQ -->
<section id="faq" class="px-4 py-20" aria-labelledby="faq-heading">
	<div class="mx-auto max-w-2xl">
		<div class="mb-10 text-center">
			<p class="mb-2 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
				Vanliga frågor om Golfkompis och Min Golf
			</p>
			<h2 id="faq-heading" class="text-3xl font-semibold tracking-tight">Vanliga frågor</h2>
			<p class="mx-auto mt-3 max-w-md text-sm text-muted-foreground">
				Allt du behöver veta om att boka golftid och bevaka avbokade starttider med Golfkompis.
			</p>
		</div>
		<Accordion type="single" class="w-full">
			{#each faqs as faq, i (faq.question)}
				<AccordionItem value="item-{i}">
					<AccordionTrigger>{faq.question}</AccordionTrigger>
					<AccordionContent>
						<p class="text-muted-foreground">{faq.answer}</p>
					</AccordionContent>
				</AccordionItem>
			{/each}
		</Accordion>
	</div>
</section>

<!-- CTA -->
<section
	id="cta"
	class="flex flex-col items-center gap-6 bg-muted/40 px-4 py-24 text-center"
	aria-labelledby="cta-heading"
>
	<h2 id="cta-heading" class="max-w-xl text-3xl font-semibold tracking-tight">
		Redo att aldrig missa en avbokad golftid igen?
	</h2>
	<p class="max-w-md text-muted-foreground">
		Skapa ett gratis konto, koppla ditt Min Golf och börja boka golftid smartare — kom igång på
		under en minut.
	</p>
	<div class="flex flex-wrap justify-center gap-3">
		<Button size="lg" href="/register">Registrera dig nu</Button>
		<Button size="lg" variant="outline" href="/login">Har redan konto</Button>
	</div>
	<p class="text-xs text-muted-foreground">Inget kreditkort · Avregistrera när som helst</p>
</section>
