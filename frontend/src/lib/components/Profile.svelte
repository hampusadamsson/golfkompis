<script lang="ts">
	import { credentials } from '$lib/auth/credentials.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import StarIcon from '@lucide/svelte/icons/star';

	const profile = $derived(credentials.profile);

	const genderLabel = $derived(
		profile?.gender === 'M' ? 'Man' : profile?.gender === 'K' || profile?.gender === 'F' ? 'Kvinna' : (profile?.gender ?? '')
	);

	const initials = $derived(
		profile ? `${profile.firstName[0] ?? ''}${profile.lastName[0] ?? ''}`.toUpperCase() : ''
	);
</script>

{#if profile}
	<section class="border rounded-xl p-4">
		<h2 class="mb-4 text-xl font-semibold">Profil</h2>

		<!-- Header row: avatar + name on left, golf ID on right -->
		<div class="flex items-center justify-between gap-4 mb-4">
			<div class="flex items-center gap-4">
				{#if profile.imageUrl}
					<img src={profile.imageUrl} alt="Profilbild" class="h-16 w-16 rounded-full object-cover" />
				{:else}
					<div class="bg-muted rounded-full h-16 w-16 flex items-center justify-center text-xl font-bold text-muted-foreground select-none shrink-0">
						{initials}
					</div>
				{/if}
				<p class="text-lg font-semibold">{profile.firstName} {profile.lastName}</p>
			</div>
			<Badge variant="secondary" class="shrink-0">{profile.golfId}</Badge>
		</div>

		<!-- Stats row: evenly distributed -->
		<div class="grid grid-cols-3 mb-4 divide-x">
			<div class="text-center px-2">
				<p class="text-2xl font-bold">{profile.hcp}</p>
				<p class="text-xs text-muted-foreground">HCP</p>
			</div>
			<div class="text-center px-2">
				<p class="text-2xl font-bold">{profile.age}</p>
				<p class="text-xs text-muted-foreground">Ålder</p>
			</div>
			<div class="text-center px-2">
				<p class="text-2xl font-bold">{genderLabel}</p>
				<p class="text-xs text-muted-foreground">Kön</p>
			</div>
		</div>

		<!-- Clubs: home club left, member badges right -->
		<div class="grid gap-4 sm:grid-cols-2 mb-4">
			{#if profile.homeClubName}
				<div>
					<p class="text-sm font-medium">{profile.homeClubName}</p>
					{#if profile.districtName}
						<p class="text-xs text-muted-foreground">{profile.districtName}</p>
					{/if}
				</div>
			{/if}
			{#if profile.memberClubs.length > 0}
				<div class="flex flex-wrap gap-1 sm:justify-end">
					{#each profile.memberClubs as club (club.id)}
						<Badge variant={club.isHomeClub ? 'default' : 'outline'} class="gap-1">
							{#if club.isHomeClub}<StarIcon class="h-3 w-3" />{/if}
							{club.name}
						</Badge>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Status badges left, email right -->
		<div class="flex flex-wrap items-center justify-between gap-4">
			<div class="flex flex-wrap gap-2">
				<Badge variant={profile.hasActiveMembership ? 'secondary' : 'destructive'}>
					{profile.hasActiveMembership ? 'Aktivt medlemskap' : 'Inaktivt medlemskap'}
				</Badge>
				{#if !profile.allowedToBook}
					<Badge variant="destructive">Får inte boka</Badge>
				{/if}
				{#if profile.capped}
					<Badge variant="outline">
						HCP-tak{profile.hardCap ? `: ${profile.hardCap}` : ''}
					</Badge>
				{/if}
				{#if profile.isFederationSuspended}
					<Badge variant="destructive">Avstängd</Badge>
				{/if}
				{#if profile.isFederationSuspendedCompetition}
					<Badge variant="destructive">Avstängd från tävling</Badge>
				{/if}
			</div>
			{#if profile.emailAddress}
				<p class="text-sm text-muted-foreground shrink-0">E-post: {profile.emailAddress}</p>
			{/if}
		</div>
	</section>
{/if}
